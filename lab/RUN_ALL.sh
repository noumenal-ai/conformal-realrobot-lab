#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TORCH_HOME="${TORCH_HOME:-$ROOT/work/torch_cache}"
export HF_HOME="${HF_HOME:-$ROOT/work/hf_cache}"
export CUBLAS_WORKSPACE_CONFIG="${CUBLAS_WORKSPACE_CONFIG:-:4096:8}"
export PYTHONHASHSEED="0"
export OMP_NUM_THREADS="1"
export MKL_NUM_THREADS="1"
export OPENBLAS_NUM_THREADS="1"
export NUMEXPR_NUM_THREADS="1"
RESUME=0
if [[ "${1:-}" == "--resume" ]]; then
  RESUME=1
elif [[ $# -ne 0 ]]; then
  echo "Usage: bash RUN_ALL.sh [--resume]" >&2
  exit 2
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "The frozen protocol requires Linux." >&2
  exit 1
fi
if ! command -v python3.10 >/dev/null 2>&1; then
  echo "python3.10 is required. Install it; do not change the protocol Python version." >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
  echo "git and curl are required." >&2
  exit 1
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "The frozen protocol requires an NVIDIA GPU and nvidia-smi." >&2
  exit 1
fi
if [[ -z "${HF_TOKEN:-${HUGGING_FACE_HUB_TOKEN:-}}" ]]; then
  echo "Export an existing Hugging Face token with access to facebook/jepa-wms; do not substitute data." >&2
  exit 1
fi
FREE_KIB="$(df -Pk "$ROOT" | awk 'NR==2 {print $4}')"
if [[ -z "$FREE_KIB" || "$FREE_KIB" -lt $((25 * 1024 * 1024)) ]]; then
  echo "At least 25 GiB free disk is required." >&2
  exit 1
fi

python3.10 "$ROOT/scripts/verify_seal.py"
python3.10 "$ROOT/scripts/verify_lean_contract.py"

mkdir -p "$ROOT/work/stamps" "$ROOT/outputs"
if [[ $RESUME -eq 0 ]] && compgen -G "$ROOT/work/stamps/*.done" >/dev/null; then
  echo "A prior run exists. Use: bash RUN_ALL.sh --resume" >&2
  exit 1
fi

run_step() {
  local name="$1"
  shift
  local stamp="$ROOT/work/stamps/${name}.done"
  if [[ $RESUME -eq 1 && -f "$stamp" ]]; then
    echo "[resume] skipping completed step: $name"
    return
  fi
  echo "[run] $name"
  "$@"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$stamp"
}

bootstrap_env() {
  if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    python3.10 -m venv "$ROOT/.venv"
  fi
  "$ROOT/.venv/bin/python" -m pip install --upgrade \
    pip==25.0.1 setuptools==75.8.0 wheel==0.45.1
  "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/environment/requirements.txt"
  "$ROOT/.venv/bin/python" -m pip install --no-deps -e "$ROOT"
}

run_step environment bootstrap_env
PY="$ROOT/.venv/bin/python"
run_step unit_tests "$PY" -m pytest "$ROOT/tests"
run_step clone_sources "$PY" "$ROOT/scripts/01_clone_sources.py"
run_step validate_upstream_contract "$PY" "$ROOT/scripts/01_validate_upstream.py"
run_step preflight "$PY" "$ROOT/scripts/00_preflight.py"
run_step fetch_assets "$PY" "$ROOT/scripts/02_fetch_assets.py"
run_step index_real_data "$PY" "$ROOT/scripts/03_index_data.py"
run_step score_frozen_world_model "$PY" "$ROOT/scripts/04_score_world_model.py"
run_step run_preregistered_battery "$PY" "$ROOT/scripts/05_run_experiment.py"
run_step analyze_and_render "$PY" "$ROOT/scripts/06_analyze.py"
run_step build_lean "$ROOT/scripts/07_build_lean.sh"
run_step final_verify "$PY" "$ROOT/scripts/08_final_verify.py"

echo "PASS: see $ROOT/outputs/HANDOFF_REPORT.md"
