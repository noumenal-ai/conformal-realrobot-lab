from __future__ import annotations

import copy
import os
import random
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import torch
import yaml

from .franka import EpisodeReader, TransitionRecord


def configure_determinism(seed: int = 0) -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if torch.cuda.is_available():
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)
    torch.use_deterministic_algorithms(True, warn_only=False)


@contextmanager
def pinned_dinov2_hub(dinov2_repo: Path) -> Iterator[None]:
    original = torch.hub.load
    local_repo = str(dinov2_repo.resolve())

    def locked_load(repo_or_dir, model, *args, **kwargs):
        if repo_or_dir == "facebookresearch/dinov2":
            kwargs.pop("source", None)
            return original(local_repo, model, *args, source="local", **kwargs)
        if str(repo_or_dir) == local_repo:
            kwargs.pop("source", None)
            return original(local_repo, model, *args, source="local", **kwargs)
        raise RuntimeError(f"Unapproved torch.hub source: {repo_or_dir}")

    torch.hub.load = locked_load
    try:
        yield
    finally:
        torch.hub.load = original


def load_frozen_dino_world_model(
    *,
    jepa_repo: Path,
    dinov2_repo: Path,
    config_relative_path: str,
    checkpoint_path: Path,
    device_name: str,
    disable_decoder_heads: bool,
):
    repo_str = str(jepa_repo.resolve())
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    from app.plan_common.datasets import get_data_stats
    from app.plan_common.datasets.preprocessor import Preprocessor
    from app.plan_common.datasets.transforms import make_inverse_transforms, make_transforms
    from app.vjepa_wm.modelcustom.simu_env_planning.vit_enc_preds import init_module

    config_path = jepa_repo / config_relative_path
    with config_path.open("r", encoding="utf-8") as f:
        args_eval = yaml.safe_load(f)
    model_kwargs = args_eval["model_kwargs"]
    cfgs_data = model_kwargs.get("data", {})
    cfgs_data_aug = model_kwargs.get("data_aug", {})
    wrapper_kwargs = model_kwargs.get("wrapper_kwargs", {})
    pretrain_kwargs = copy.deepcopy(model_kwargs.get("pretrain_kwargs", {}))
    if disable_decoder_heads:
        # Decoder heads do not enter the frozen latent prediction or score. Removing them
        # avoids downloading an unused image decoder while leaving encoder/predictor weights
        # and the upstream model computation unchanged.
        pretrain_kwargs["heads_cfg"] = {}

    if not torch.cuda.is_available():
        raise RuntimeError("The frozen protocol requires a CUDA-capable NVIDIA GPU")
    device = torch.device(device_name)
    torch.cuda.set_device(device)

    stats = get_data_stats("droid")
    img_size = int(cfgs_data.get("img_size", 224))
    transform = make_transforms(
        img_size=img_size,
        normalize=cfgs_data_aug.get("normalize", [[0.485, 0.456, 0.406], [0.229, 0.224, 0.225]]),
        random_horizontal_flip=False,
        random_resize_aspect_ratio=(1.0, 1.0),
        random_resize_scale=(1.0, 1.0),
        reprob=0.0,
        auto_augment=False,
        motion_shift=False,
    )
    inverse_transform = make_inverse_transforms(img_size=img_size, **cfgs_data_aug)
    preprocessor = Preprocessor(
        action_mean=torch.tensor(stats["action_mean"]),
        action_std=torch.tensor(stats["action_std"]),
        state_mean=torch.tensor(stats["state_mean"]),
        state_std=torch.tensor(stats["state_std"]),
        proprio_mean=torch.tensor(stats["proprio_mean"]),
        proprio_std=torch.tensor(stats["proprio_std"]),
        transform=transform,
        inverse_transform=inverse_transform,
    )

    with pinned_dinov2_hub(dinov2_repo):
        model = init_module(
            folder=str(checkpoint_path.parent),
            checkpoint=checkpoint_path.name,
            model_kwargs=pretrain_kwargs,
            wrapper_kwargs=wrapper_kwargs,
            cfgs_data=cfgs_data,
            device=device,
            action_dim=int(stats["action_dim"]),
            proprio_dim=int(stats["proprio_dim"]),
            preprocessor=preprocessor,
        )
    model.eval()
    model.to(device)
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model, preprocessor


def _visual_tensor(batch: np.ndarray, device: torch.device) -> torch.Tensor:
    if batch.ndim != 5 or batch.shape[-1] != 3:
        raise ValueError(f"Expected [B,T,H,W,3] RGB batch, got {batch.shape}")
    tensor = torch.from_numpy(batch).permute(0, 1, 4, 2, 3).contiguous()
    return tensor.to(device=device, dtype=torch.float32, non_blocking=True)


@torch.no_grad()
def score_records(
    *,
    model,
    records: Sequence[TransitionRecord],
    data_root: Path,
    camera_key: str,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    device = model.device
    scores: list[np.ndarray] = []
    pooled_context: list[np.ndarray] = []

    with EpisodeReader(data_root, camera_key) as reader:
        for start in range(0, len(records), batch_size):
            chunk = records[start : start + batch_size]
            contexts: list[np.ndarray] = []
            targets: list[np.ndarray] = []
            actions: list[np.ndarray] = []
            for record in chunk:
                context, target = reader.load_visuals(record)
                contexts.append(context)
                targets.append(target)
                actions.append(
                    np.stack(
                        [
                            np.asarray(record.context_action, dtype=np.float32),
                            np.asarray(record.action, dtype=np.float32),
                        ],
                        axis=0,
                    )
                )

            context_batch = _visual_tensor(np.stack(contexts, axis=0), device)
            target_batch = _visual_tensor(np.stack(targets, axis=0), device)
            action_batch = torch.from_numpy(np.stack(actions, axis=0)).to(device=device, dtype=torch.float32)

            z_context = model.encode(context_batch)
            z_target = model.encode(target_batch)
            action_features = model.model.encode_act(action_batch)
            if z_context.shape[1] != action_features.shape[1]:
                raise RuntimeError(
                    "Context/action alignment failed: "
                    f"{z_context.shape[1]} visual steps vs {action_features.shape[1]} action steps"
                )
            predicted, _, _ = model.model.forward_pred(z_context, action_features, None)
            pred_next = predicted[:, -1]
            target_next = z_target[:, 0]
            if pred_next.shape != target_next.shape:
                raise RuntimeError(
                    f"Latent shape mismatch: predicted {tuple(pred_next.shape)}, target {tuple(target_next.shape)}"
                )
            error = pred_next - target_next
            dims = tuple(range(1, error.ndim))
            score = torch.sqrt(torch.mean(error.square(), dim=dims))
            context_last = z_context[:, -1]
            pooled = context_last.mean(dim=tuple(range(1, context_last.ndim - 1)))

            scores.append(score.detach().cpu().numpy().astype(np.float64))
            pooled_context.append(pooled.detach().cpu().numpy().astype(np.float32))

    all_scores = np.concatenate(scores, axis=0)
    all_context = np.concatenate(pooled_context, axis=0)
    if all_scores.shape != (len(records),):
        raise RuntimeError(f"Expected {len(records)} scores, got {all_scores.shape}")
    if not np.isfinite(all_scores).all() or (all_scores < 0).any():
        raise RuntimeError("World-model scores must be finite and nonnegative")
    return all_scores, all_context
