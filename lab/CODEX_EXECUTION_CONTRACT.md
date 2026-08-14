# Execution contract for Codex

You are the laboratory execution process. All scientific decisions are complete. Do not conduct
research, browse for alternatives, redesign the protocol, tune parameters, substitute datasets,
change models, remove failed cells, or reinterpret the theorem. Your job is command execution,
mechanical debugging, and proof-term completion only.

## Permitted actions

1. Run `bash RUN_ALL.sh` from this directory.
2. Supply existing credentials through `HF_TOKEN` when the official gated dataset requires it.
3. If and only if the Lean gate stops at an `AUTOFORMALIZE_ONLY` proof body, edit proof terms
   in the files listed in `lean/ALLOW_EDIT.txt`.
4. Use only the lemma names and proof routes in `lean/PROOF_ROUTES.md`, the extracted local
   supplied archives, Mathlib, and Loogle for name resolution.
5. Re-run `bash RUN_ALL.sh --resume` until all gates pass.
6. Return the generated `outputs/HANDOFF_REPORT.md` and the output directory unchanged.

## Forbidden actions

- Do not edit `config/`, `src/`, `scripts/`, `THEORY.md`, or `SCIENTIFIC_PROTOCOL.md`.
- Do not change any theorem statement, definition signature, import, namespace, toolchain, or
  Mathlib pin.
- Do not introduce `sorry`, `admit`, `axiom`, `unsafe`, `native_decide`, or an unverified
  external theorem.
- Do not create simulated data, perturb observations, generate outcomes, or train/fine-tune the
  world model.
- Do not use a different camera, task subset, score, shift, seed, alpha, sample size, clipping
  value, or classifier.
- Do not suppress a failing repetition or result cell.
- Do not fetch from a host outside `config/sources.lock.yaml`.
- Do not declare success unless all three artifacts exist and say or record PASS:
  `outputs/results/VALIDATION_REPORT.md`, `outputs/lean/LEAN_BUILD_REPORT.md`, and
  `outputs/HANDOFF_REPORT.md`.

The sealed-manifest gate detects changes to scientific and experiment files. Lean statement
hashes are checked independently, so changing the proposition to make a proof easier will fail.
