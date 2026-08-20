import FiniteExpectation
import Mathlib.Tactic

noncomputable section

namespace PolicyShift

/-- Odds of a probability `u`. -/
def odds (u : ℝ) : ℝ := u / (1 - u)

/-- Density ratio recovered from a domain posterior `u` under target-domain prior `ρ`. -/
def ratioFromPosterior (ρ u : ℝ) : ℝ := ((1 - ρ) / ρ) * odds u

/-- Source-domain weight of index `i`, expressed against the balanced-mixture mass. -/
def sourceMass {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η : ι → ℝ) (ρ : ℝ) (i : ι) : ℝ :=
  M.prob i * (1 - η i) / (1 - ρ)

/-- A difference of odds is the difference of the probabilities divided by the product of
their complements. -/
theorem odds_sub_odds (u v : ℝ) (hu : u ≠ 1) (hv : v ≠ 1) :
    odds u - odds v = (u - v) / ((1 - u) * (1 - v)) := by
  unfold odds
  have hu0 : 1 - u ≠ 0 := sub_ne_zero.mpr hu.symm
  have hv0 : 1 - v ≠ 0 := sub_ne_zero.mpr hv.symm
  field_simp [hu0, hv0]
  ring

end PolicyShift

end
