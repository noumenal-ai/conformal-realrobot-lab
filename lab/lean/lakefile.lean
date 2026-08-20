import Lake
open Lake DSL

package policyShift where
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"

@[default_target]
lean_lib PolicyShift where
  srcDir := "src"
  roots := #[
    `FiniteExpectation,
    `BinaryPinsker,
    `OddsDifference,
    `DoInterventionParents,
    `Main]
