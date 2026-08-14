from __future__ import annotations

import shutil

from ccwm_lab.io_utils import load_yaml, project_root
from ccwm_lab.report import analyze_and_report


def main() -> None:
    root = project_root()
    protocol = load_yaml(root / "config" / "protocol.yaml")
    _, passed = analyze_and_report(
        results_csv=root / "outputs" / "results" / "replicate_results.csv",
        pool_csv=root / "outputs" / "results" / "pool_with_shift.csv",
        protocol=protocol,
        output_dir=root / "outputs" / "results",
    )
    fragments = root / "outputs" / "results" / "paper_fragments"
    fragments.mkdir(parents=True, exist_ok=True)
    for name in [
        "theory_domain_classifier.tex",
        "methods_real_robot.tex",
        "interpretation_guardrails.md",
        "references_addendum.bib",
        "final_results_schema.json",
    ]:
        shutil.copy2(root / "templates" / name, fragments / name)
    if not passed:
        raise SystemExit("Mechanical validation failed; inspect outputs/results/VALIDATION_REPORT.md")


if __name__ == "__main__":
    main()
