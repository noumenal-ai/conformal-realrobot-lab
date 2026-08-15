# External source ledger

The execution package contains no dataset or pretrained model bytes. It clones/downloads only
the sources below, verifies Git commits, uses predeclared immutable Hugging Face revisions, and records
SHA-256 hashes in the run manifest.

## World model and real evaluation data

### `facebookresearch/jepa-wms`

- Locked Git commit: `13cf1d9c7e476f53c17714d2e0f1dc239a883ce0`.
- Upstream role: PyTorch world-model implementation, official DINO-WM checkpoint loader,
  DROID/Franka preprocessing, and the exact real-robot evaluation configuration.
- Fixed checkpoint: `facebook/jepa-wms:dino_wm_droid.pth.tar`.
- Locked model revision: `9b9c41ef249466630dbf1a20e78391865d07b3b9`.
- Fixed dataset subtree: `facebook/jepa-wms` dataset repository, `franka_custom/**`.
- Locked dataset revision: `6116f042ae7ae4c8e3f1fd2f194f432615664182`.
- The upstream README identifies pretrained JEPA-WM/DINO-WM models for DROID and exposes
  official Hugging Face/fbaipublicfiles weights.
- The upstream downloader identifies `franka_custom` as an official dataset target.
- The frozen upstream DINO-WM config uses `Franka_hf`, 4 Hz, camera
  `exterior_image_2_left`, context window 2, and unnormalized seven-dimensional DROID-format
  actions. This package copies those choices exactly.

### `facebookresearch/dinov2`

- Locked Git commit: `7764ea0f912e53c92e82eb78a2a1631e92725fc8`.
- Role: the frozen DINOv2 ViT-S/14 visual encoder required by the released DINO-WM.
- It is loaded from the local locked clone; the upstream code is not allowed to resolve an
  unpinned Git branch.
- Official backbone URL: `dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`.
- Locked backbone SHA-256:
  `b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9`.
  Execution stops if the official download does not match.

## Supplied Lean libraries

### Measurements archive

- Source repository: Dhruv Gupta,
  [`Zetetic-Dhruv/zetesis-puremath`](https://github.com/Zetetic-Dhruv/zetesis-puremath).
- Included archive: `measurements(2).zip`.
- Locked SHA-256: `4535226e6b52804c0c72a214263c9fa8e35da9971395c08b0083b5c8bc598d60`.
- Lean: `leanprover/lean4:v4.30.0-rc2`.
- Mathlib source: [`leanprover-community/mathlib4`](https://github.com/leanprover-community/mathlib4),
  commit `2c53994ec06c7197a0f05dd85e8aae96e454efb8`.
- Used declarations:
  - `InformationTheory.binary_pinsker`;
  - `InformationTheory.pinsker_proof`;
  - `ProbabilityTheory.FintypePMF.trueExpectation`;
  - finite PMF TV/transfer declarations;
  - real total variation definitions.

### Causality archive

- Source repository: Causality sub-library of
  [`noumenal-ai/design-lab`](https://github.com/noumenal-ai/design-lab).
- Included archive: `causality.zip`.
- Locked SHA-256: `10d36e640eb12c57feb716d775b1e203cbeeeb8c06c574a5a1bd7084477a1a61`.
- Lean: `leanprover/lean4:v4.31.0`.
- Mathlib source: [`leanprover-community/mathlib4`](https://github.com/leanprover-community/mathlib4),
  commit `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
- Used declarations:
  - `Causality.SCM`;
  - `Causality.SCM.doIntervene`.

The archives have incompatible Lean/Mathlib pins. They are deliberately built in two isolated
Lake workspaces. No attempt is made to merge or silently port them.

## Statistical references

1. Ryan Tibshirani, Rina Foygel Barber, Emmanuel Candes, and Aaditya Ramdas.
   *Conformal Prediction Under Covariate Shift*. NeurIPS 2019.
2. Aditya Menon and Cheng Soon Ong. *Linking Losses for Density Ratio and
   Class-Probability Estimation*. ICML 2016.
3. Peter Bartlett and Shahar Mendelson. *Rademacher and Gaussian Complexities: Risk Bounds
   and Structural Results*. JMLR 2002.
4. The supplied ZPM binary and general Pinsker formalizations.

## License handling

The source repositories and Hugging Face assets retain their own licenses. The setup script
copies license files into `outputs/provenance/licenses/` and the final report lists the exact
asset revisions. This package does not redistribute their model or data bytes.

## Exact upstream file map checked by `scripts/01_validate_upstream.py`

At the locked commits, the runner mechanically checks these files before any data/model work:

- `facebookresearch/jepa-wms/README.md`: released DINO-WM/JEPA-WM model table and official model
  download routes.
- `facebookresearch/jepa-wms/src/scripts/download_data.py`: `franka_custom/*` official dataset
  target in the gated `facebook/jepa-wms` dataset repository.
- `facebookresearch/jepa-wms/configs/evals/simu_env_planning/droid/dino-wm/`
  `droid_L2_cem_sourcedset_H3_nas3_maxnorm01_ctxt2_gH3_r224_alpha0_ep64_decode.yaml`:
  predictor, encoder, Franka validation set, camera, 4 Hz, context, action normalization, and exact
  episode manifest patterns.
- `facebookresearch/jepa-wms/evals/utils.py`: deterministic evaluation resize/aspect settings.
- `facebookresearch/jepa-wms/src/utils/yaml_utils.py`: direct `ruamel.yaml` import used by the exact model-loading chain; the package pins that minimal dependency.
- `facebookresearch/jepa-wms/app/plan_common/datasets/droid_dset.py`: HDF5 observation keys,
  30 Hz source assumption, and the released `poses_to_diffs` action construction.
- `facebookresearch/jepa-wms/hubconf.py`: released `dino_wm_droid` model entry and checkpoint route.
- `facebookresearch/dinov2/dinov2/hub/backbones.py` and `dinov2/hub/utils.py`: official
  DINOv2 ViT-S/14 URL construction.

A mismatch aborts execution. The coding agent is not allowed to reinterpret a changed upstream
interface.
