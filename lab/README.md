# Conformal Counterfactuals real-robot lab package

This is a frozen execution package for one real-data, real-model experiment and two isolated
Lean builds. It is designed so an execution agent performs laboratory work only.

## One command

The exact supplied `measurements(2).zip` and `causality.zip` are included and hash-locked.
Authenticate to Hugging Face for the official gated real-robot dataset, then run:

```bash
export HF_TOKEN=YOUR_EXISTING_TOKEN
bash RUN_ALL.sh
```

After a partial failure, fix only the permitted Lean proof bodies if necessary and run:

```bash
bash RUN_ALL.sh --resume
```

## Fixed external substrate

- Real data: official `franka_custom` physical-robot trajectories released by
  `facebookresearch/jepa-wms`, locked to Hugging Face revision
  `6116f042ae7ae4c8e3f1fd2f194f432615664182`.
- Fixed model: official pretrained `dino_wm_droid` DINO-WM, locked to Hugging Face revision
  `9b9c41ef249466630dbf1a20e78391865d07b3b9`.
- Visual encoder: pinned local clone of `facebookresearch/dinov2`.
- No simulator, toy predictor, generated transition, generated image, or synthetic noise model.

## Expected resources

- Linux with an NVIDIA CUDA GPU.
- Python 3.10.
- Roughly 25 GB free disk for environment, source, model cache, and the official real-robot
  dataset.
- Network access to the allowlisted official GitHub, Hugging Face, PyPI/PyTorch, and Lean hosts.
- The two included, hash-locked Lean archives.

## Output

A successful run creates:

- raw transition index and frozen model scores;
- every preregistered repetition/cell as CSV and JSON;
- paper-ready LaTeX table, theorem/method fragments, bibliography addendum, and PDF/PNG figures;
- exact L1, TV, logistic-regret, ESS, and coverage-bound diagnostics;
- Git/Hugging Face revisions, file hashes, hardware and package versions;
- two Lean build logs and axiom/sorry audits;
- `outputs/HANDOFF_REPORT.md`.

Codex reads `AGENTS.md`; for a direct handoff, paste `CODEX_PROMPT.txt` verbatim. The package boundary and local
validation status are recorded in `PACKAGE_AUDIT.md`; all output formulas are frozen in
`STATISTICAL_TOOLKIT.md`; the exact Lean claim boundary is in
`lean/FORMALIZATION_SCOPE.md`.
