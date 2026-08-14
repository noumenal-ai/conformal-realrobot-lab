from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import torch

from ccwm_lab.io_utils import load_yaml, project_root


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    if protocol["execution"]["require_linux"] and platform.system() != "Linux":
        raise SystemExit("Frozen protocol requires Linux")
    if sys.version_info[:2] != (3, 10):
        raise SystemExit(f"Frozen protocol requires Python 3.10, got {sys.version}")
    if protocol["execution"]["require_nvidia_gpu"]:
        if shutil.which("nvidia-smi") is None or not torch.cuda.is_available():
            raise SystemExit("Frozen protocol requires an NVIDIA GPU visible to PyTorch")
    free = shutil.disk_usage(root).free
    if free < 25 * 1024**3:
        raise SystemExit(f"At least 25 GiB free disk is required; found {free / 1024**3:.1f} GiB")
    if not (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")):
        raise SystemExit(
            "HF_TOKEN is required for the official gated facebook/jepa-wms dataset. "
            "Obtain access yourself, export the existing token, and rerun; do not substitute data."
        )
    print(f"Python: {sys.version.split()[0]}")
    print(f"Torch: {torch.__version__}")
    print(f"CUDA: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Free disk GiB: {free / 1024**3:.1f}")


if __name__ == "__main__":
    main()
