import Lake
open Lake DSL

package CCWMCausal where
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"

lean_lib Causality where
  roots := #[`Causality]

lean_lib ConformalCounterfactuals where
  roots := #[`ConformalCounterfactuals.CommonState, `ConformalCounterfactuals.Intervention]

@[default_target]
lean_lib ConformalCounterfactualsCausal where
  roots := #[`ConformalCounterfactualsCausal]
