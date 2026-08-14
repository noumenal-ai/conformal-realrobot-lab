import Causality.Architecture

namespace ConformalCounterfactuals

open Causality

/-- The supplied `SCM.doIntervene` clears incoming parents at an intervened vertex. -/
theorem doIntervene_clears_parents
    (M : SCM) (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) (i : M.V) (hi : i ∈ X) :
    (M.doIntervene X x).Pa i = ∅ := by
  -- BEGIN AUTOFORMALIZE_ONLY doIntervene_clears_parents
  simp [Causality.SCM.doIntervene, hi]
  rfl
  -- END AUTOFORMALIZE_ONLY doIntervene_clears_parents

/-- Away from the intervention set, the supplied construction preserves the parent set. -/
theorem doIntervene_preserves_other_parents
    (M : SCM) (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) (i : M.V) (hi : i ∉ X) :
    (M.doIntervene X x).Pa i = M.Pa i := by
  -- BEGIN AUTOFORMALIZE_ONLY doIntervene_preserves_other_parents
  simp [Causality.SCM.doIntervene, hi]
  -- END AUTOFORMALIZE_ONLY doIntervene_preserves_other_parents

end ConformalCounterfactuals
