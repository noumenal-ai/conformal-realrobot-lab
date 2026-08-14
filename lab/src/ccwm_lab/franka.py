from __future__ import annotations

import hashlib
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

import h5py
import numpy as np


@dataclass(frozen=True)
class TransitionRecord:
    sample_id: str
    episode_id: str
    task: str
    relative_h5_path: str
    context_indices: tuple[int, ...]
    target_index: int
    current_state: tuple[float, ...]
    context_action: tuple[float, ...]
    action: tuple[float, ...]
    translation_action_norm: float
    rotation_action_norm: float
    gripper_action_abs: float

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["context_indices"] = list(self.context_indices)
        row["current_state"] = list(self.current_state)
        row["context_action"] = list(self.context_action)
        row["action"] = list(self.action)
        return row


def _import_poses_to_diffs(jepa_repo: Path):
    repo_str = str(jepa_repo.resolve())
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    from app.plan_common.datasets.droid_dset import poses_to_diffs

    return poses_to_diffs


def discover_episode_files(data_root: Path, patterns: list[str]) -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in patterns:
        for path in data_root.glob(pattern):
            if path.is_file() and path.suffix == ".h5":
                found[str(path.resolve())] = path.resolve()
    return [found[k] for k in sorted(found)]


def _read_states(h5: h5py.File, cartesian_key: str, gripper_key: str) -> np.ndarray:
    if cartesian_key not in h5:
        raise KeyError(f"Missing cartesian key {cartesian_key}")
    if gripper_key not in h5:
        raise KeyError(f"Missing gripper key {gripper_key}")
    cart = np.asarray(h5[cartesian_key], dtype=np.float64)
    grip = np.asarray(h5[gripper_key], dtype=np.float64)
    if grip.ndim == 1:
        grip = grip[:, None]
    if cart.ndim != 2 or cart.shape[1] != 6:
        raise ValueError(f"Expected cartesian positions with shape [T,6], got {cart.shape}")
    if grip.ndim != 2 or grip.shape[1] != 1 or grip.shape[0] != cart.shape[0]:
        raise ValueError(f"Expected gripper positions with shape [T,1], got {grip.shape}")
    state = np.concatenate([cart, grip], axis=1)
    if not np.isfinite(state).all():
        raise ValueError("Non-finite robot state detected")
    return state


def _select_evenly(values: list[int], maximum: int) -> list[int]:
    if len(values) <= maximum:
        return values
    positions = np.linspace(0, len(values) - 1, num=maximum)
    selected = sorted({values[int(round(pos))] for pos in positions})
    if len(selected) != maximum:
        # This fallback is deterministic and is reached only through duplicate rounding.
        selected = [values[i] for i in np.linspace(0, len(values), maximum, endpoint=False, dtype=int)]
    return selected


def index_real_transitions(
    *,
    data_root: Path,
    jepa_repo: Path,
    patterns: list[str],
    camera_key: str,
    cartesian_key: str,
    gripper_key: str,
    source_fps: int,
    evaluation_fps: int,
    context_frames: int,
    horizon: int,
    max_windows_per_episode: int,
) -> tuple[list[TransitionRecord], dict[str, Any]]:
    if context_frames != 2 or horizon != 1:
        raise ValueError("The frozen protocol requires exactly two context frames and horizon one")
    if source_fps <= 0 or evaluation_fps <= 0:
        raise ValueError("Frame rates must be positive")
    frame_step = math.ceil(source_fps / evaluation_fps)
    poses_to_diffs = _import_poses_to_diffs(jepa_repo)
    episodes = discover_episode_files(data_root, patterns)
    records: list[TransitionRecord] = []
    episode_summaries: list[dict[str, Any]] = []

    for episode_path in episodes:
        relative = episode_path.relative_to(data_root)
        episode_id = hashlib.sha256(str(relative).encode("utf-8")).hexdigest()[:16]
        task = str(relative.parent)
        with h5py.File(episode_path, "r") as h5:
            if camera_key not in h5:
                raise KeyError(f"Missing camera key {camera_key} in {relative}")
            image_dataset = h5[camera_key]
            image_shape = image_dataset.shape
            if image_dataset.dtype != np.dtype("uint8"):
                raise ValueError(
                    f"Expected upstream RGB bytes with dtype uint8 in {relative}, got {image_dataset.dtype}"
                )
            if len(image_shape) != 4 or image_shape[-1] != 3:
                raise ValueError(f"Expected RGB image array [T,H,W,3] in {relative}, got {image_shape}")
            states = _read_states(h5, cartesian_key, gripper_key)
            n = min(int(image_shape[0]), int(states.shape[0]))
        earliest_target = context_frames * frame_step
        target_indices = list(range(earliest_target, n, frame_step))
        target_indices = _select_evenly(target_indices, max_windows_per_episode)
        episode_count = 0
        for target_idx in target_indices:
            context = tuple(target_idx - frame_step * k for k in range(context_frames, 0, -1))
            if context != (target_idx - 2 * frame_step, target_idx - frame_step):
                raise AssertionError("Frozen context indexing invariant failed")
            context_pose_pair = states[[context[0], context[1]], :]
            context_action = np.asarray(poses_to_diffs(context_pose_pair), dtype=np.float64)
            pose_pair = states[[context[-1], target_idx], :]
            action = np.asarray(poses_to_diffs(pose_pair), dtype=np.float64)
            if context_action.shape != (1, 7) or action.shape != (1, 7):
                raise ValueError(
                    "Upstream poses_to_diffs must return (1,7) for both aligned actions; "
                    f"got {context_action.shape} and {action.shape}"
                )
            previous_a = context_action[0]
            a = action[0]
            current = states[context[-1]]
            if not np.isfinite(previous_a).all() or not np.isfinite(a).all():
                raise ValueError(f"Non-finite aligned action in {relative} at target {target_idx}")
            identity = f"{relative}|{','.join(map(str, context))}|{target_idx}"
            sample_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
            records.append(
                TransitionRecord(
                    sample_id=sample_id,
                    episode_id=episode_id,
                    task=task,
                    relative_h5_path=str(relative),
                    context_indices=context,
                    target_index=target_idx,
                    current_state=tuple(float(v) for v in current),
                    context_action=tuple(float(v) for v in previous_a),
                    action=tuple(float(v) for v in a),
                    translation_action_norm=float(np.linalg.norm(a[:3])),
                    rotation_action_norm=float(np.linalg.norm(a[3:6])),
                    gripper_action_abs=float(abs(a[6])),
                )
            )
            episode_count += 1
        episode_summaries.append(
            {
                "episode_id": episode_id,
                "relative_h5_path": str(relative),
                "task": task,
                "raw_frames": n,
                "indexed_windows": episode_count,
            }
        )

    records.sort(key=lambda r: (r.relative_h5_path, r.target_index))
    metadata = {
        "data_root": str(data_root.resolve()),
        "camera_key": camera_key,
        "source_fps": source_fps,
        "evaluation_fps": evaluation_fps,
        "frame_step": frame_step,
        "context_frames": context_frames,
        "horizon": horizon,
        "episode_count": len(episodes),
        "transition_count": len(records),
        "episodes": episode_summaries,
    }
    return records, metadata


class EpisodeReader:
    def __init__(self, data_root: Path, camera_key: str):
        self.data_root = data_root
        self.camera_key = camera_key
        self._files: dict[str, h5py.File] = {}

    def _get_file(self, relative_path: str) -> h5py.File:
        if relative_path not in self._files:
            self._files[relative_path] = h5py.File(self.data_root / relative_path, "r")
        return self._files[relative_path]

    def load_visuals(self, record: TransitionRecord) -> tuple[np.ndarray, np.ndarray]:
        h5 = self._get_file(record.relative_h5_path)
        dataset = h5[self.camera_key]
        if dataset.dtype != np.dtype("uint8"):
            raise ValueError(f"Expected upstream RGB bytes for {record.sample_id}, got {dataset.dtype}")
        context = np.asarray(dataset[list(record.context_indices)])
        target = np.asarray(dataset[[record.target_index]])
        if context.ndim != 4 or target.ndim != 4:
            raise ValueError(f"Unexpected image rank for {record.sample_id}")
        return context, target

    def close(self) -> None:
        for h5 in self._files.values():
            h5.close()
        self._files.clear()

    def __enter__(self) -> "EpisodeReader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def record_from_dict(row: dict[str, Any]) -> TransitionRecord:
    return TransitionRecord(
        sample_id=str(row["sample_id"]),
        episode_id=str(row["episode_id"]),
        task=str(row["task"]),
        relative_h5_path=str(row["relative_h5_path"]),
        context_indices=tuple(int(v) for v in row["context_indices"]),
        target_index=int(row["target_index"]),
        current_state=tuple(float(v) for v in row["current_state"]),
        context_action=tuple(float(v) for v in row["context_action"]),
        action=tuple(float(v) for v in row["action"]),
        translation_action_norm=float(row["translation_action_norm"]),
        rotation_action_norm=float(row["rotation_action_norm"]),
        gripper_action_abs=float(row["gripper_action_abs"]),
    )
