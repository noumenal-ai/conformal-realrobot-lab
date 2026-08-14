from __future__ import annotations

import json
from pathlib import Path
import os

import numpy as np
import pandas as pd
import torch

from ccwm_lab.franka import record_from_dict
from ccwm_lab.io_utils import atomic_write_json, load_yaml, project_root, read_jsonl, sha256_file
from ccwm_lab.world_model import configure_determinism, load_frozen_dino_world_model, score_records


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    source_lock = load_yaml(root / "config" / "sources.lock.yaml")
    model_cfg = protocol["source_model"]
    data_cfg = protocol["dataset"]
    configure_determinism(0)

    records = [record_from_dict(row) for row in read_jsonl(root / "outputs" / "raw" / "transition_index.jsonl")]
    checkpoint = root / "work" / "assets" / "jepa_wms_model" / model_cfg["checkpoint_filename"]
    model, _ = load_frozen_dino_world_model(
        jepa_repo=root / "work" / "external" / "jepa_wms",
        dinov2_repo=root / "work" / "external" / "dinov2",
        config_relative_path=str(model_cfg["config_path"]),
        checkpoint_path=checkpoint,
        device_name=str(model_cfg["device"]),
        disable_decoder_heads=bool(model_cfg["disable_decoder_heads"]),
    )
    scores, pooled_context = score_records(
        model=model,
        records=records,
        data_root=root / "work" / "assets" / data_cfg["asset_key"] / data_cfg["local_subdir"],
        camera_key=str(data_cfg["camera_key"]),
        batch_size=int(model_cfg["batch_size"]),
    )
    rows = []
    for record, score in zip(records, scores):
        row = record.to_dict()
        row["score"] = float(score)
        rows.append(row)
    frame = pd.DataFrame(rows)
    raw = root / "outputs" / "raw"
    frame.to_csv(raw / "scored_pool.csv", index=False)
    np.save(raw / "pooled_context_embeddings.npy", pooled_context)
    torch_home = Path(os.environ.get("TORCH_HOME", root / "work" / "torch_cache"))
    backbone_spec = source_lock["pytorch_hub_assets"]["dinov2_vits14"]
    backbone_matches = sorted(torch_home.rglob(str(backbone_spec["filename"])))
    if len(backbone_matches) != 1:
        raise RuntimeError(
            f"Expected exactly one locked DINOv2 backbone file named {backbone_spec['filename']}, "
            f"found {backbone_matches}"
        )
    backbone_path = backbone_matches[0]
    backbone_sha = sha256_file(backbone_path)
    if backbone_sha != str(backbone_spec["sha256"]):
        raise RuntimeError(
            f"DINOv2 backbone hash mismatch: expected {backbone_spec['sha256']}, got {backbone_sha}"
        )
    encoder_cache = []
    if torch_home.exists():
        for path in sorted(p for p in torch_home.rglob("*") if p.is_file()):
            if ".git" in path.parts:
                continue
            encoder_cache.append(
                {
                    "relative_path": str(path.relative_to(torch_home)),
                    "sha256": sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    atomic_write_json(
        raw / "model_scoring_metadata.json",
        {
            "model": model_cfg["name"],
            "score": model_cfg["score"],
            "action_alignment": data_cfg["action_alignment"],
            "checkpoint_sha256": sha256_file(checkpoint),
            "dinov2_backbone_url": backbone_spec["url"],
            "dinov2_backbone_sha256": backbone_sha,
            "torch_hub_cache_files": encoder_cache,
            "transition_count": len(records),
            "embedding_shape": list(pooled_context.shape),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    )
    print(f"Scored {len(records)} real transitions with frozen {model_cfg['name']}")


if __name__ == "__main__":
    main()
