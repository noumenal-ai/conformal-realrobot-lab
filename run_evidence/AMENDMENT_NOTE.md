# Conformal Real-Robot Lab v6 amendment note

The original v1 package remains preserved unchanged.

This execution package retains the two v3 dependency repairs:

- `packaging==24.2` to `packaging==25.0`, satisfying the declared
  `pyvers==0.1.0` requirement `packaging>=25.0,<26.0` selected through
  `tensordict==0.9.1`.
- Added `opencv-python==4.11.0.86`, because the locked JEPA-WMS commit declares
  `opencv-python` and its imported transform implementation requires `cv2`.

OpenCV 4.11.0.86 is used instead of the newer 4.12 line because its published Python 3.10
metadata accepts the protocol's frozen `numpy==1.26.4`.

After v3 authenticated and downloaded all 33 locked files, indexing found exactly 192 eligible
real transitions and stopped at the original minimum of 256 before model scoring. On 2026-08-15,
the investigator explicitly authorized execution with the observed pool. V4 therefore changes:

- `experiment_id` from `ccwm-real-franka-dinowm-v1` to
  `ccwm-real-franka-dinowm-v2-pool192`;
- `dataset.min_pool_size` from 256 to 192; and
- the corresponding documented mechanical gate and amendment record.

No episode allowlist, indexing rule, model, shift, sampling, seed, method, theorem, test, or
analysis gate changed. Calibration and test samples are already defined as draws with replacement,
so their configured sizes do not require a pool containing that many distinct transitions.

V4 then indexed all 192 transitions from 15 episodes and reached the frozen model before failing
without emitting a score. The released predictor requires the visual and action time dimensions to
match; V4 supplied two visual context steps and one action step. V5 repairs that interface by
deriving both consecutive actions from the three observed poses, passing two aligned visual/action
steps through the locked teacher-forced predictor, and scoring only its final next-frame output.
The one-transition GPU smoke test produced matching predicted/target latent shapes and a finite
score. The experiment identifier is now `ccwm-real-franka-dinowm-v3-pool192-actionaligned`.

V5 completed model scoring, the full statistical battery, and analysis with `FINAL STATUS: PASS`.
Its statistical Lean proofs also compiled, but the causal Lake package omitted the
`ConformalCounterfactuals` library that owns `CommonState` and `Intervention`; consequently the
default target could not resolve its own imported module prefix. V6 adds only that missing library
declaration with the two existing module roots. No theorem statement, proof, toolchain, dependency
pin, scientific configuration, Python code, result, or experiment identifier changed.

The complete `SEALED_SHA256SUMS.json` is regenerated for this amended package. The seal, Lean
contract, archive integrity, and dependency resolution must pass before relaunch.

Deployment note: the retained v5 virtualenv is moved into the v6 root to avoid reinstalling the
large frozen environment. Because it contains an editable install, the deployment harness must
immediately reinstall the local package with `--no-build-isolation --no-deps -e` at the v6 path.
Disabling build isolation reuses the already locked build tooling and requires no network access.
Otherwise Python's
project-root resolver continues to name v5 and prepares the vendored Lean source trees in the
wrong directory. This is a harness relocation repair only; it does not modify the sealed package
or any scientific artifact.

The first complete Lean pass also exposed a final-verifier self-reference: the verifier scanned
its own source file and therefore matched the forbidden-generator names that define its blacklist.
The scan now excludes only `scripts/08_final_verify.py` itself while continuing to inspect every
Python file under `src/` and all other files under `scripts/`. No experiment or data-producing code
is excluded. The sealed hash for the verifier is updated accordingly.
