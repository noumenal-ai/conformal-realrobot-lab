from __future__ import annotations

from pathlib import Path

from ccwm_lab.io_utils import atomic_write_json, load_yaml, project_root
from ccwm_lab.provenance import clone_locked_repo


def main() -> None:
    root = project_root()
    lock = load_yaml(root / "config" / "sources.lock.yaml")
    external = root / "work" / "external"
    result = {}
    for key, spec in lock["repositories"].items():
        result[key] = clone_locked_repo(external / key, str(spec["url"]), str(spec["commit"]))
    atomic_write_json(root / "work" / "git_sources.resolved.json", result)


if __name__ == "__main__":
    main()
