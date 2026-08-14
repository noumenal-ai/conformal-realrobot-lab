from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .io_utils import atomic_write_json, load_yaml, run_checked, sha256_file


def clone_locked_repo(destination: Path, url: str, commit: str) -> dict[str, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        run_checked(["git", "clone", "--filter=blob:none", "--no-checkout", url, str(destination)])
    if not (destination / ".git").exists():
        raise RuntimeError(f"Destination exists but is not a Git clone: {destination}")
    run_checked(["git", "fetch", "--force", "origin", commit], cwd=destination)
    run_checked(["git", "checkout", "--detach", "--force", commit], cwd=destination)
    run_checked(["git", "clean", "-ffd"], cwd=destination)
    head = run_checked(["git", "rev-parse", "HEAD"], cwd=destination).stdout.strip()
    if head != commit:
        raise RuntimeError(f"Git pin mismatch for {destination}: expected {commit}, got {head}")
    dirty = run_checked(["git", "status", "--porcelain"], cwd=destination).stdout.strip()
    if dirty:
        raise RuntimeError(f"Locked repository is dirty after checkout: {destination}\n{dirty}")
    origin = run_checked(["git", "remote", "get-url", "origin"], cwd=destination).stdout.strip()
    if origin.rstrip("/") != url.rstrip("/"):
        raise RuntimeError(f"Origin mismatch for {destination}: expected {url}, got {origin}")
    return {"url": origin, "commit": head}


def verify_locked_repo(destination: Path, url: str, commit: str) -> None:
    if not (destination / ".git").exists():
        raise RuntimeError(f"Missing locked repository: {destination}")
    head = run_checked(["git", "rev-parse", "HEAD"], cwd=destination).stdout.strip()
    origin = run_checked(["git", "remote", "get-url", "origin"], cwd=destination).stdout.strip()
    dirty = run_checked(["git", "status", "--porcelain"], cwd=destination).stdout.strip()
    if head != commit or origin.rstrip("/") != url.rstrip("/") or dirty:
        raise RuntimeError(
            f"Repository guard failed for {destination}: head={head}, origin={origin}, dirty={bool(dirty)}"
        )


def _hf_token() -> str | None:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


def resolve_and_download_assets(
    lock_path: Path,
    assets_root: Path,
    resolved_lock_path: Path,
) -> dict[str, Any]:
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download

    lock = load_yaml(lock_path)
    api = HfApi(token=_hf_token())
    resolved: dict[str, Any] = {"assets": {}}
    assets_root.mkdir(parents=True, exist_ok=True)

    for key, spec in lock["huggingface_assets"].items():
        repo_id = str(spec["repo_id"])
        repo_type = str(spec["repo_type"])
        revision = str(spec["revision"])
        info = api.repo_info(repo_id=repo_id, repo_type=repo_type, revision=revision)
        resolved_sha = str(info.sha)
        if resolved_sha != revision:
            raise RuntimeError(
                f"Hugging Face revision mismatch for {repo_id}: expected {revision}, got {resolved_sha}"
            )
        entry: dict[str, Any] = {
            "repo_id": repo_id,
            "repo_type": repo_type,
            "revision": revision,
            "role": spec["role"],
            "files": [],
        }
        target = assets_root / key
        target.mkdir(parents=True, exist_ok=True)
        if "filenames" in spec:
            for filename in spec["filenames"]:
                path = Path(
                    hf_hub_download(
                        repo_id=repo_id,
                        repo_type=repo_type,
                        filename=filename,
                        revision=revision,
                        local_dir=target,
                    )
                )
                entry["files"].append(
                    {
                        "relative_path": str(path.relative_to(target)),
                        "sha256": sha256_file(path),
                        "size_bytes": path.stat().st_size,
                    }
                )
        else:
            allow_patterns = [str(p) for p in spec["allow_patterns"]]
            snapshot_download(
                repo_id=repo_id,
                repo_type=repo_type,
                revision=revision,
                allow_patterns=allow_patterns,
                local_dir=target,
            )
            for path in sorted(p for p in target.rglob("*") if p.is_file()):
                if ".cache" in path.parts:
                    continue
                entry["files"].append(
                    {
                        "relative_path": str(path.relative_to(target)),
                        "sha256": sha256_file(path),
                        "size_bytes": path.stat().st_size,
                    }
                )
        if not entry["files"]:
            raise RuntimeError(f"Official asset download produced no files for {key}")
        resolved["assets"][key] = entry

    atomic_write_json(resolved_lock_path, resolved)
    return resolved


def copy_source_licenses(lock_path: Path, external_root: Path, output_root: Path) -> None:
    lock = load_yaml(lock_path)
    dst = output_root / "provenance" / "licenses"
    dst.mkdir(parents=True, exist_ok=True)
    for key, spec in lock["repositories"].items():
        source = external_root / key / str(spec["license_file"])
        if not source.exists():
            raise RuntimeError(f"Missing license file for {key}: {source}")
        shutil.copy2(source, dst / f"{key}_{source.name}")


def git_metadata(lock_path: Path, external_root: Path) -> dict[str, Any]:
    lock = load_yaml(lock_path)
    out: dict[str, Any] = {}
    for key, spec in lock["repositories"].items():
        repo = external_root / key
        verify_locked_repo(repo, str(spec["url"]), str(spec["commit"]))
        out[key] = {
            "url": spec["url"],
            "commit": spec["commit"],
            "role": spec["role"],
        }
    return out
