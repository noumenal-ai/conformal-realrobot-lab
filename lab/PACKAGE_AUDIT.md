# Package audit and handoff boundary

## Locked mathematical result

For a domain prior `rho in (0,1)`, mixture `M=(1-rho)P+rho Q`, Bayes domain posterior `eta`, and a
fitted posterior `h in [gamma,1-gamma]`, define

    what_h = ((1-rho)/rho) h/(1-h).

The package fixes and proves on paper the exact identity

    E_P |w-what_h| = (1/rho) E_M[|eta-h|/(1-h)]

and therefore, using binary Pinsker for Bernoulli log-loss regret `Delta_log(h)`,

    E_P |w-what_h| <= (1/(rho gamma)) sqrt(Delta_log(h)/2).

For `rho=1/2` this is `sqrt(2 Delta_log(h))/gamma`. Composed with the paper's
approximate-weight conformal transfer theorem, target coverage is at least

    1-alpha-(1/(rho gamma)) sqrt(Delta_log(h)/2).

`THEORY.md` contains the full proof, scope, finite-sample interface, and exact finite-pool
interface. The Lean files freeze the corresponding finite-support statements and proof routes.

## Locked empirical substrate

- Model code: `facebookresearch/jepa-wms` at commit
  `13cf1d9c7e476f53c17714d2e0f1dc239a883ce0`.
- Visual encoder code: `facebookresearch/dinov2` at commit
  `7764ea0f912e53c92e82eb78a2a1631e92725fc8`; official ViT-S/14 backbone bytes are locked to
  SHA-256 `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`.
- Model checkpoint: official `facebook/jepa-wms` `dino_wm_droid.pth.tar` at revision
  `9b9c41ef249466630dbf1a20e78391865d07b3b9`.
- Real data: official `facebook/jepa-wms` dataset `franka_custom/**` at revision
  `6116f042ae7ae4c8e3f1fd2f194f432615664182`.
- Exact upstream evaluation choices: DINO-WM DROID configuration, physical Franka evaluation
  data, 4 Hz, `exterior_image_2_left`, two context frames, horizon one, and a seven-dimensional unnormalized DROID-format delta-pose
  action covariate reconstructed by the released upstream routine.

No pretrained model or dataset bytes are redistributed in the package. The two user-supplied
Lean archives are included verbatim and SHA-256 locked.

## Local checks completed before packaging

- Python source compilation.
- Six deterministic algebra/algorithm unit tests: posterior-ratio identity, theorem inequality,
  finite tilt, weighted conformal quantile, ESS, Wilson interval, and outcome-blind rank statistic.
  These fixtures are not empirical evidence and contain no toy predictor or generated outcome.
- Shell syntax checks for the one-command runner and Lean builder.
- Full non-network experiment/report pipeline dry-run against an ephemeral interface fixture; no
  fixture or generated result is included in the deliverable.
- Lean statement/import contract hashing and verification.
- Included Lean archive SHA-256 verification.
- Static review of the exact pinned upstream HDF5, model, action, transform, and checkpoint routes.
- No generated experiment result is included.

## Checks intentionally deferred to the execution machine

The external real-data experiment, GPU model scoring, official asset downloads, pinned upstream
import smoke test, and Lean kernel builds require the investigator's Linux/CUDA/Hugging Face/Lean
environment. They have not been claimed as executed in this packaging environment. `RUN_ALL.sh`
performs them and refuses to produce a PASS handoff unless all experiment and Lean gates succeed.

## Permitted execution-agent discretion

None on science or experimental design. The only nonmechanical edits allowed are Lean proof terms
inside the marked `AUTOFORMALIZE_ONLY` regions, using the locked proof routes. The statement hash
gate rejects theorem or import changes; the package seal rejects changes elsewhere. `AGENTS.md`
and `CODEX_PROMPT.txt` reduce the handoff to one command plus mechanical Lean proof-body filling.
