#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

"$PY" "$ROOT/scripts/07_prepare_lean.py"
"$PY" "$ROOT/scripts/verify_lean_contract.py"

if ! command -v elan >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain none
fi
# shellcheck disable=SC1090
source "$HOME/.elan/env"
mkdir -p "$ROOT/outputs/lean"

build_one() {
  local workspace="$1"
  local audit="$2"
  local log="$3"
  (
    cd "$workspace"
    lake update
    lake exe cache get
    lake build
    lake env lean "$audit"
  ) 2>&1 | tee "$log"
}

build_one "$ROOT/lean/statistical" \
  "ConformalCounterfactuals/AxiomAudit.lean" \
  "$ROOT/outputs/lean/statistical_build.log"
build_one "$ROOT/lean/causal" \
  "ConformalCounterfactuals/AxiomAudit.lean" \
  "$ROOT/outputs/lean/causal_build.log"

for log in "$ROOT/outputs/lean/statistical_build.log" "$ROOT/outputs/lean/causal_build.log"; do
  if grep -Eiq 'sorryAx|declaration uses.*sorry|unsolved goals' "$log"; then
    echo "Lean audit log contains an unresolved proof marker: $log" >&2
    exit 1
  fi
done

"$PY" "$ROOT/scripts/verify_lean_contract.py" --final
printf 'FINAL STATUS: PASS\n' > "$ROOT/outputs/lean/LEAN_BUILD_REPORT.md"
