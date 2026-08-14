from __future__ import annotations

from ccwm_lab.io_utils import project_root
from ccwm_lab.provenance import resolve_and_download_assets


def main() -> None:
    root = project_root()
    resolve_and_download_assets(
        root / "config" / "sources.lock.yaml",
        root / "work" / "assets",
        root / "work" / "assets.resolved.json",
    )


if __name__ == "__main__":
    main()
