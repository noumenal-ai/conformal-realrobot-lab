from __future__ import annotations

from pathlib import Path
import importlib
import sys

from ccwm_lab.io_utils import atomic_write_json, load_yaml, project_root


def require_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise RuntimeError(f"Locked upstream contract mismatch for {label}: expected {expected!r}, got {actual!r}")


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    jepa = root / "work" / "external" / "jepa_wms"
    dinov2 = root / "work" / "external" / "dinov2"
    config_path = jepa / str(protocol["source_model"]["config_path"])
    if not config_path.is_file():
        raise RuntimeError(f"Missing locked upstream model config: {config_path}")
    config = load_yaml(config_path)
    model = config["model_kwargs"]
    pretrain = model["pretrain_kwargs"]
    data = model["data"]

    require_equal("predictor", pretrain["predictor"]["pred_type"], "dino_wm")
    require_equal("visual encoder type", pretrain["visual_encoder"]["enc_type"], "dino")
    require_equal("visual encoder version", pretrain["visual_encoder"]["enc_version"], "dinov2_vits14")
    require_equal("image size", data["img_size"], 224)
    require_equal("encoder tubelet size", pretrain["tubelet_size_enc"], 1)
    require_equal("predicted frame capacity", pretrain["num_frames_pred"], 4)
    require_equal("action conditioning", pretrain["action_conditioning"], "feature")
    require_equal("action embedding dimension", pretrain["action_encoder"]["action_emb_dim"], 10)
    require_equal("batchified visual encoder", pretrain["wm_encoding"]["batchify_video"], True)
    require_equal("latent representation normalization", pretrain["wm_encoding"]["normalize_reps"], False)
    require_equal("validation dataset", data["validation"]["val_datasets"], ["Franka_hf"])
    require_equal(
        "validation camera",
        data["validation"]["val_dataset_camera_views"],
        ["exterior_image_2_left"],
    )
    require_equal("DROID sampling fps", data["droid"]["fps"], 4)
    require_equal("DROID frames per clip", data["droid"]["dataset_fpcs"], [4])
    require_equal("context window", model["wrapper_kwargs"]["ctxt_window"], 2)
    require_equal("frame skip", data["custom"]["frameskip"], 1)
    require_equal("action skip", data["custom"]["action_skip"], 1)
    require_equal("action normalization", data["custom"]["normalize_action"], False)
    require_equal("pixel normalization", model["data_aug"]["normalize"], [[0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])
    require_equal(
        "manifest patterns",
        data["droid"]["mpk_manifest_patterns"],
        protocol["dataset"]["allowed_episode_globs"],
    )

    loader = (jepa / "app/plan_common/datasets/droid_dset.py").read_text(encoding="utf-8")
    for literal in [
        'trajectory["episode_data"]["observation"][camera_view]',
        '"cartesian_position"',
        '"gripper_position"',
        "def poses_to_diffs",
        "vfps = 30",
    ]:
        if literal not in loader:
            raise RuntimeError(f"Locked upstream DROID/Franka loader contract missing: {literal}")


    eval_utils = (jepa / "evals/utils.py").read_text(encoding="utf-8")
    for literal in [
        "random_resize_aspect_ratio=(1.0, 1.0)",
        "random_resize_scale=(1.0, 1.0)",
    ]:
        if literal not in eval_utils:
            raise RuntimeError(f"Locked upstream evaluation transform contract missing: {literal}")

    downloader = (jepa / "src/scripts/download_data.py").read_text(encoding="utf-8")
    if "franka_custom" not in downloader or "facebook/jepa-wms" not in downloader:
        raise RuntimeError("Pinned upstream downloader no longer identifies the locked Franka dataset")

    hubconf = (jepa / "hubconf.py").read_text(encoding="utf-8")
    if '"dino_wm_droid"' not in hubconf or "droid_dino-wm_noprop.pth.tar" not in hubconf:
        raise RuntimeError("Locked upstream hubconf no longer exposes the expected DINO-WM DROID model")
    if not (dinov2 / "hubconf.py").is_file():
        raise RuntimeError("Pinned DINOv2 clone lacks hubconf.py")
    dinov2_utils = (dinov2 / "dinov2/hub/utils.py").read_text(encoding="utf-8")
    dinov2_backbones = (dinov2 / "dinov2/hub/backbones.py").read_text(encoding="utf-8")
    expected_backbone_url = load_yaml(root / "config" / "sources.lock.yaml")["pytorch_hub_assets"][
        "dinov2_vits14"
    ]["url"]
    if '_DINOV2_BASE_URL = "https://dl.fbaipublicfiles.com/dinov2"' not in dinov2_utils:
        raise RuntimeError("Pinned DINOv2 source no longer exposes the locked official base URL")
    if 'f"/{model_base_name}/{model_full_name}_pretrain.pth"' not in dinov2_backbones:
        raise RuntimeError("Pinned DINOv2 source no longer constructs the expected backbone URL")
    if not expected_backbone_url.endswith("/dinov2_vits14/dinov2_vits14_pretrain.pth"):
        raise RuntimeError("Source lock contains an unexpected DINOv2 backbone URL")

    # Import exactly the code path used later, before downloading large assets. This is a
    # dependency/interface smoke test only; it does not instantiate or alter the model.
    for repo in [dinov2, jepa]:
        repo_text = str(repo.resolve())
        if repo_text not in sys.path:
            sys.path.insert(0, repo_text)
    for module_name in [
        "app.plan_common.datasets.droid_dset",
        "app.plan_common.datasets.preprocessor",
        "app.plan_common.datasets.transforms",
        "app.vjepa_wm.modelcustom.simu_env_planning.vit_enc_preds",
        "dinov2.hub.backbones",
    ]:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            raise RuntimeError(f"Pinned upstream import smoke test failed for {module_name}: {exc}") from exc

    atomic_write_json(
        root / "work" / "upstream_contract.json",
        {
            "status": "PASS",
            "model_config": str(config_path.relative_to(jepa)),
            "predictor": "dino_wm",
            "encoder": "dinov2_vits14",
            "real_dataset": "Franka_hf/franka_custom",
            "camera": "exterior_image_2_left",
            "fps": 4,
            "context_window": 2,
            "action_normalization": False,
            "manifest_pattern_count": len(protocol["dataset"]["allowed_episode_globs"]),
        },
    )
    print("Pinned upstream model/data contract verified")


if __name__ == "__main__":
    main()
