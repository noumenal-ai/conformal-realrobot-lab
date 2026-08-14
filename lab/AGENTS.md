# Codex laboratory instructions

This repository is a sealed laboratory protocol, not a research workspace.

## Mandatory action

Run exactly:

```bash
bash RUN_ALL.sh
```

If a completed step exists and the run stopped, run exactly:

```bash
bash RUN_ALL.sh --resume
```

## Read-only files

Everything is read-only except the proof bodies bounded by matching
`BEGIN AUTOFORMALIZE_ONLY` / `END AUTOFORMALIZE_ONLY` markers in the files listed in
`lean/ALLOW_EDIT.txt`.

Do not alter theorem statements, imports, namespaces, toolchains, Mathlib pins, protocol values,
Python code, shell code, source locks, tests, result schemas, or validation gates. The seal and
contract hashes enforce this.

## Lean task

When a marked proof body is the only failure:

1. Read `lean/PROOF_ROUTES.md`.
2. Use only the copied supplied Lean libraries, the pinned Mathlib dependency, and Loogle for an
   exact Mathlib name.
3. Replace only `exact _` inside the marked body.
4. Do not add declarations or dependencies.
5. Never use `sorry`, `admit`, `axiom`, `unsafe`, or `native_decide`.
6. Resume the fixed runner.

## Prohibited behavior

Do not search for another dataset or model. Do not tune, simplify, skip, reinterpret, or repair a
scientific failure. Do not manufacture a PASS file. If a non-Lean scientific or validation gate
fails, preserve the logs and report the failure to the investigator.

Success exists only when `outputs/HANDOFF_REPORT.md` says `FINAL STATUS: PASS` and the final seal,
experiment validation, and both Lean builds have passed.
