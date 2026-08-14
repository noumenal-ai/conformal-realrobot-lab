from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from ccwm_lab.io_utils import (
    atomic_write_json,
    environment_metadata,
    load_yaml,
    project_root,
    run_checked,
    sha256_file,
)
from ccwm_lab.provenance import copy_source_licenses, git_metadata


def _required_outputs(root: Path) -> list[Path]:
    output = root / "outputs"
    results = output / "results"
    figures = results / "figures"
    fragments = results / "paper_fragments"
    required = [
        output / "raw" / "transition_index.jsonl",
        output / "raw" / "transition_index_metadata.json",
        output / "raw" / "scored_pool.csv",
        output / "raw" / "pooled_context_embeddings.npy",
        output / "raw" / "model_scoring_metadata.json",
        results / "pool_with_shift.csv",
        results / "replicate_results.csv",
        results / "classifier_fits.csv",
        results / "shift_laws.csv",
        results / "summary.csv",
        results / "summary.json",
        results / "pool_episode_cluster_bootstrap.csv",
        results / "main_results_table.tex",
        results / "VALIDATION_REPORT.md",
        fragments / "theory_domain_classifier.tex",
        fragments / "methods_real_robot.tex",
        fragments / "interpretation_guardrails.md",
        fragments / "references_addendum.bib",
        fragments / "final_results_schema.json",
        output / "lean" / "statistical_build.log",
        output / "lean" / "causal_build.log",
        output / "lean" / "LEAN_BUILD_REPORT.md",
        root / "work" / "upstream_contract.json",
        root / "work" / "assets.resolved.json",
        root / "work" / "git_sources.resolved.json",
        root / "work" / "lean_sources.resolved.json",
    ]
    for stem in ["coverage_vs_shift", "certificate_diagnostics", "ess_vs_shift", "radius_vs_shift"]:
        required.extend([figures / f"{stem}.pdf", figures / f"{stem}.png"])
    return required


def _final_static_guards(root: Path) -> None:
    run_checked([sys.executable, str(root / "scripts" / "verify_seal.py")])
    run_checked([sys.executable, str(root / "scripts" / "verify_lean_contract.py"), "--final"])


def main() -> None:
    root = project_root()
    output = root / "outputs"
    _final_static_guards(root)

    missing = [str(path) for path in _required_outputs(root) if not path.is_file()]
    if missing:
        raise SystemExit("Missing required outputs:\n" + "\n".join(missing))
    if "FINAL STATUS: PASS" not in (output / "results" / "VALIDATION_REPORT.md").read_text():
        raise SystemExit("Experiment validation did not pass")
    if "FINAL STATUS: PASS" not in (output / "lean" / "LEAN_BUILD_REPORT.md").read_text():
        raise SystemExit("Lean build did not pass")

    forbidden_generators = [
        r"np\.random\.normal",
        r"np\.random\.uniform",
        r"torch\.randn",
        r"random\.gauss",
        r"make_blobs",
        r"synthetic_dataset",
    ]
    scanned: list[str] = []
    for folder in [root / "src", root / "scripts"]:
        for path in folder.rglob("*.py"):
            if path.resolve() == Path(__file__).resolve():
                continue
            text = path.read_text(encoding="utf-8")
            scanned.append(path.relative_to(root).as_posix())
            for pattern in forbidden_generators:
                if re.search(pattern, text):
                    raise SystemExit(f"Forbidden synthetic generator {pattern} in {path}")

    lock_path = root / "config" / "sources.lock.yaml"
    provenance_dir = output / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    copy_source_licenses(lock_path, root / "work" / "external", output)
    git_info = git_metadata(lock_path, root / "work" / "external")
    for name in [
        "assets.resolved.json",
        "lean_sources.resolved.json",
        "git_sources.resolved.json",
        "upstream_contract.json",
    ]:
        shutil.copy2(root / "work" / name, provenance_dir / name)
    freeze = run_checked([sys.executable, "-m", "pip", "freeze"]).stdout
    (provenance_dir / "pip_freeze.txt").write_text(freeze, encoding="utf-8")

    metadata = environment_metadata()
    try:
        gpu = run_checked(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ]
        ).stdout.strip()
    except Exception:
        gpu = "unavailable"
    manifest = {
        "status": "PASS",
        "experiment_id": load_yaml(root / "config" / "protocol.yaml")["experiment_id"],
        "git_sources": git_info,
        "assets": json.loads((root / "work" / "assets.resolved.json").read_text()),
        "lean_sources": json.loads((root / "work" / "lean_sources.resolved.json").read_text()),
        "upstream_contract": json.loads((root / "work" / "upstream_contract.json").read_text()),
        "environment": metadata,
        "gpu": gpu,
        "synthetic_generator_scan": {"status": "PASS", "files": scanned},
        "final_seal": "PASS",
        "lean_contract": "PASS",
    }
    atomic_write_json(output / "run_manifest.json", manifest)

    report = f"""# Codex laboratory handoff report

FINAL STATUS: PASS

## Frozen result substrate

- External real dataset: official `facebook/jepa-wms` `franka_custom` trajectories.
- External model: official `dino_wm_droid` checkpoint.
- Model implementation commit: `{git_info['jepa_wms']['commit']}`.
- DINOv2 implementation commit: `{git_info['dinov2']['commit']}`.
- No simulated transition, generated image, target, score, simulator, or toy predictor was used.
- The action covariate was deterministically reconstructed from observed robot poses by the locked upstream routine.

## Deliverables

- `outputs/results/summary.csv`
- `outputs/results/replicate_results.csv`
- `outputs/results/classifier_fits.csv`
- `outputs/results/shift_laws.csv`
- `outputs/results/main_results_table.tex`
- `outputs/results/figures/`
- `outputs/results/paper_fragments/`
- `outputs/results/VALIDATION_REPORT.md`
- `outputs/lean/LEAN_BUILD_REPORT.md`
- `outputs/run_manifest.json`
- `outputs/provenance/output_hashes.json`

The experiment and both isolated Lean workspaces passed every mechanical gate. The final seal and
Lean statement contract were rechecked after execution. Scientific interpretation remains with
the investigator; the execution agent made no protocol decisions.
"""
    (output / "HANDOFF_REPORT.md").write_text(report, encoding="utf-8")

    output_hashes = {}
    hash_manifest = provenance_dir / "output_hashes.json"
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p != hash_manifest):
        relative = path.relative_to(root).as_posix()
        output_hashes[relative] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    atomic_write_json(hash_manifest, output_hashes)


if __name__ == "__main__":
    main()
