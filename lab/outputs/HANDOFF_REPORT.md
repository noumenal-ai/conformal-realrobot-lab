# Codex laboratory handoff report

FINAL STATUS: PASS

## Frozen result substrate

- External real dataset: official `facebook/jepa-wms` `franka_custom` trajectories.
- External model: official `dino_wm_droid` checkpoint.
- Model implementation commit: `13cf1d9c7e476f53c17714d2e0f1dc239a883ce0`.
- DINOv2 implementation commit: `7764ea0f912e53c92e82eb78a2a1631e92725fc8`.
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
