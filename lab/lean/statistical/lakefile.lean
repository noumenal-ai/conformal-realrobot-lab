import Lake
open Lake DSL

package CCWMStat where
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "2c53994ec06c7197a0f05dd85e8aae96e454efb8"

lean_lib ZPM where
  roots := #[`ZPM]

@[default_target]
lean_lib ConformalCounterfactuals where
  roots := #[`ConformalCounterfactuals]
