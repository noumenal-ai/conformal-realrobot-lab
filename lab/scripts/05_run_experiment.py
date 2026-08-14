from __future__ import annotations

from ccwm_lab.experiment import run_experiment_battery
from ccwm_lab.io_utils import load_yaml, project_root


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    run_experiment_battery(
        scored_pool_csv=root / "outputs" / "raw" / "scored_pool.csv",
        protocol=protocol,
        output_dir=root / "outputs" / "results",
    )


if __name__ == "__main__":
    main()
