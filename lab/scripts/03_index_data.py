from __future__ import annotations

from ccwm_lab.franka import index_real_transitions
from ccwm_lab.io_utils import atomic_write_json, load_yaml, project_root, write_jsonl


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    cfg = protocol["dataset"]
    data_root = root / "work" / "assets" / cfg["asset_key"] / cfg["local_subdir"]
    records, metadata = index_real_transitions(
        data_root=data_root,
        jepa_repo=root / "work" / "external" / "jepa_wms",
        patterns=[str(v) for v in cfg["allowed_episode_globs"]],
        camera_key=str(cfg["camera_key"]),
        cartesian_key=str(cfg["cartesian_key"]),
        gripper_key=str(cfg["gripper_key"]),
        source_fps=int(cfg["source_fps"]),
        evaluation_fps=int(cfg["evaluation_fps"]),
        context_frames=int(cfg["context_frames"]),
        horizon=int(cfg["horizon"]),
        max_windows_per_episode=int(cfg["max_windows_per_episode"]),
    )
    if metadata["episode_count"] < int(cfg["min_episodes"]):
        raise SystemExit(f"Only {metadata['episode_count']} episodes found; minimum is {cfg['min_episodes']}")
    if metadata["transition_count"] < int(cfg["min_pool_size"]):
        raise SystemExit(f"Only {metadata['transition_count']} transitions found; minimum is {cfg['min_pool_size']}")
    raw = root / "outputs" / "raw"
    write_jsonl(raw / "transition_index.jsonl", (record.to_dict() for record in records))
    atomic_write_json(raw / "transition_index_metadata.json", metadata)
    print(f"Indexed {len(records)} real transitions from {metadata['episode_count']} real episodes")


if __name__ == "__main__":
    main()
