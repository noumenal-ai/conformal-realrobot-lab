import Causality.Architecture
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Tactic

/-!
Finite common-state one-step propensity identity. This is the causal specialization, separate
from the general density-ratio experiment.
-/

namespace ConformalCounterfactuals

open scoped BigOperators
open Finset

/-- With a shared outer state law and shared transition kernel, action propensity reweighting is
an exact change of measure. No normalization assumptions are needed for this algebraic identity. -/
theorem common_state_propensity_identity
    {S A Y : Type*} [Fintype S] [Fintype A] [Fintype Y]
    (μ : S → ℝ) (πb πt : S → A → ℝ) (K : S → A → Y → ℝ)
    (f : S → A → Y → ℝ)
    (hpos : ∀ s a, 0 < πb s a) :
    (∑ s : S, ∑ a : A, ∑ y : Y, μ s * πt s a * K s a y * f s a y)
      = ∑ s : S, ∑ a : A, ∑ y : Y,
          μ s * πb s a * K s a y * ((πt s a / πb s a) * f s a y) := by
  -- BEGIN AUTOFORMALIZE_ONLY common_state_propensity_identity
  apply Finset.sum_congr rfl
  intro s hs
  apply Finset.sum_congr rfl
  intro a ha
  apply Finset.sum_congr rfl
  intro y hy
  have hne : πb s a ≠ 0 := ne_of_gt (hpos s a)
  field_simp [hne]
  <;> ring
  -- END AUTOFORMALIZE_ONLY common_state_propensity_identity

end ConformalCounterfactuals
