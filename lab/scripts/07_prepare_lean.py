from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from ccwm_lab.io_utils import atomic_write_json, load_yaml, project_root, sha256_file


def locate_archive(root: Path, env_name: str, accepted: list[str]) -> Path:
    explicit = os.environ.get(env_name)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"{env_name} does not point to a file: {path}")
        return path
    for directory in [root, root.parent, Path.cwd()]:
        for basename in accepted:
            candidate = directory / basename
            if candidate.is_file():
                return candidate.resolve()
    raise FileNotFoundError(
        f"Could not locate one of {accepted}. Set {env_name} to the supplied archive path."
    )


def extract_clean(archive: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(destination)
    mac = destination / "__MACOSX"
    if mac.exists():
        shutil.rmtree(mac)


def find_parent_with(root: Path, child_name: str) -> Path:
    candidates = [path.parent for path in root.rglob(child_name) if path.is_dir() and "__MACOSX" not in path.parts]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one parent containing {child_name} under {root}, found {candidates}")
    return candidates[0]


def replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".DS_Store", "__MACOSX"))


def main() -> None:
    root = project_root()
    lock = load_yaml(root / "config" / "sources.lock.yaml")
    measurements_spec = lock["local_lean_archives"]["measurements"]
    causality_spec = lock["local_lean_archives"]["causality"]
    measurements_zip = locate_archive(root, "MEASUREMENTS_ZIP", list(measurements_spec["accepted_basenames"]))
    causality_zip = locate_archive(root, "CAUSALITY_ZIP", list(causality_spec["accepted_basenames"]))
    if sha256_file(measurements_zip) != str(measurements_spec["sha256"]):
        raise RuntimeError("Supplied measurements archive hash does not match the locked artifact")
    if sha256_file(causality_zip) != str(causality_spec["sha256"]):
        raise RuntimeError("Supplied causality archive hash does not match the locked artifact")

    extraction = root / "work" / "lean_sources"
    measurements_extract = extraction / "measurements"
    causality_extract = extraction / "causality"
    extract_clean(measurements_zip, measurements_extract)
    extract_clean(causality_zip, causality_extract)
    measurements_root = find_parent_with(measurements_extract, "ZPM")
    causality_root = find_parent_with(causality_extract, "Causality")

    statistical = root / "lean" / "statistical"
    causal = root / "lean" / "causal"
    replace_tree(measurements_root / "ZPM", statistical / "ZPM")
    if not (measurements_root / "ZPM.lean").is_file():
        raise RuntimeError("Supplied measurements archive lacks ZPM.lean")
    shutil.copy2(measurements_root / "ZPM.lean", statistical / "ZPM.lean")
    replace_tree(causality_root / "Causality", causal / "Causality")
    if not (causality_root / "Causality.lean").is_file():
        raise RuntimeError("Supplied causality archive lacks Causality.lean")
    shutil.copy2(causality_root / "Causality.lean", causal / "Causality.lean")

    atomic_write_json(
        root / "work" / "lean_sources.resolved.json",
        {
            "measurements": {
                "archive": str(measurements_zip),
                "sha256": sha256_file(measurements_zip),
                "root": str(measurements_root),
                "toolchain": measurements_spec["lean_toolchain"],
                "mathlib_commit": measurements_spec["mathlib_commit"],
            },
            "causality": {
                "archive": str(causality_zip),
                "sha256": sha256_file(causality_zip),
                "root": str(causality_root),
                "toolchain": causality_spec["lean_toolchain"],
                "mathlib_commit": causality_spec["mathlib_commit"],
            },
        },
    )


if __name__ == "__main__":
    main()
