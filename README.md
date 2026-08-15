# Conformal Real-Robot Lab v1 — theory result parcel

FINAL STATUS: PASS

Run ID: `ccwm-realrobot-v6-leanroot-20260814-193749`

This parcel joins the final sealed laboratory source, the complete returned outputs, the completed
Lean formalization, the pinned supplied Lean archives, and mechanical completion evidence. The run
used 192 indexed transitions from 15 official real Franka episodes and the frozen released
`dino_wm_droid` world model.

The repository includes the derived transition index, frozen-model scores, context embeddings,
statistical tables, figures, and provenance hashes. It does not redistribute the gated upstream
RGB trajectory archive or model weights; their immutable Hugging Face revisions and hashes are
recorded under `lab/config/` and `lab/outputs/provenance/`.

## Headline result

At nominal coverage 0.90 (`alpha = 0.10`):

| Shift lambda | Exact TV | Unweighted coverage | Estimated-ratio coverage | Oracle-ratio coverage |
|---:|---:|---:|---:|---:|
| 0.0 | 0.000 | 0.902 | 0.903 | 0.902 |
| 0.5 | 0.246 | 0.816 | 0.906 | 0.905 |
| 1.0 | 0.464 | 0.690 | 0.918 | 0.918 |
| 1.5 | 0.637 | 0.550 | 0.909 | 0.910 |

Under increasing finite-pool covariate shift, unweighted conformal coverage degrades while the
preregistered estimated-ratio correction remains close to the oracle and nominal target.

Both isolated Lean workspaces passed their builds and axiom audits. The statistical development
formalizes the posterior-ratio algebra, binary-Pinsker-to-mean bound, classifier-regret ratio bound,
and coverage composition. The causal development formalizes the common-state propensity identity
and the supplied intervention parent-set properties.

The statistical workspace vendors the binary-Pinsker and finite-PMF modules from Dhruv Gupta's
[`zetesis-puremath`](https://github.com/Zetetic-Dhruv/zetesis-puremath) Lean repository. The causal
workspace vendors the SCM intervention architecture from the Causality sub-library of
[`noumenal-ai/design-lab`](https://github.com/noumenal-ai/design-lab), whose exact released snapshot
is preserved in [`lab/causality.zip`](lab/causality.zip). Both workspaces build against separately
pinned revisions of [`mathlib4`](https://github.com/leanprover-community/mathlib4); the archive
digests and dependency pins are recorded in [`lab/SOURCES.md`](lab/SOURCES.md).

## Contents

- `lab/outputs/`: complete results, raw model scores, figures, paper fragments, reports, provenance,
  environment record, and per-output hashes.
- `lab/lean/`: final completed Lean source, contract hashes, proof routes, toolchains, and Lake files.
- `lab/measurements(2).zip` and `lab/causality.zip`: pinned supplied Lean dependency archives.
- `lab/THEORY.md`, `lab/STATISTICAL_TOOLKIT.md`, and `lab/SCIENTIFIC_PROTOCOL.md`: theory and
  frozen protocol documents.
- `run_evidence/`: amendment record, GCS completion marker, and all twelve runner completion stamps.

The investigator-authorized amendments and infrastructure repairs are recorded in
`run_evidence/AMENDMENT_NOTE.md`. The GCP VM was deleted only after the outputs were downloaded and
verified.

## Mechanical verification

From `lab/`:

```bash
python3 scripts/verify_seal.py
python3 scripts/verify_lean_contract.py --final
```

`outputs/provenance/output_hashes.json` records the SHA-256 digest and byte size of every finalized
output artifact other than the hash manifest itself.
