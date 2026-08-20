import Mathlib.MeasureTheory.Measure.ProbabilityMeasure
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.Data.Finset.Basic

universe u

namespace PolicyShift

open MeasureTheory ProbabilityTheory

/-- Each vertex's value is a measurable function of its parents' values and its own
exogenous noise, the noise across vertices drawn from a single joint law. -/
structure SCM : Type (u + 1) where
  /-- Vertex set. -/
  V        : Type u
  [V_fin   : Fintype V]
  [V_dec   : DecidableEq V]
  /-- Per-vertex measurable value space. -/
  Sp       : V → Type u
  [Sp_meas : ∀ i, MeasurableSpace (Sp i)]
  /-- Endogenous parent set of each vertex. -/
  Pa       : V → Finset V
  /-- Per-vertex exogenous noise space. -/
  U        : V → Type u
  [U_meas  : ∀ i, MeasurableSpace (U i)]
  /-- Joint exogenous noise distribution. -/
  uDist    : ProbabilityMeasure (∀ i : V, U i)
  /-- Structural equation sending the parent valuation and own noise to the vertex value. -/
  f        : ∀ i, ((j : { j : V // j ∈ Pa i }) → Sp j.val) × U i → Sp i
  /-- Joint measurability of each structural equation. -/
  hf       : ∀ i, Measurable (f i)

namespace SCM

variable (M : SCM)

instance : Fintype M.V := M.V_fin
instance : DecidableEq M.V := M.V_dec
instance (i : M.V) : MeasurableSpace (M.Sp i) := M.Sp_meas i
instance (i : M.V) : MeasurableSpace (M.U i) := M.U_meas i

/-- The surgery `do(X = x)`: vertices in `X` take fixed values and lose their incoming edges. -/
noncomputable def doIntervene (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) : SCM where
  V        := M.V
  V_fin    := M.V_fin
  V_dec    := M.V_dec
  Sp       := M.Sp
  Sp_meas  := M.Sp_meas
  Pa       := fun i => if i ∈ X then ∅ else M.Pa i
  U        := M.U
  U_meas   := M.U_meas
  uDist    := M.uDist
  f        := fun i inp =>
    if h : i ∈ X then x i h
    else
      M.f i ⟨fun j => inp.1 ⟨j.val, by rw [if_neg h]; exact j.property⟩, inp.2⟩
  hf       := fun i => by
    by_cases h : i ∈ X
    · simp only [dif_pos h]; exact measurable_const
    · simp only [dif_neg h]
      refine (M.hf i).comp (Measurable.prodMk ?_ measurable_snd)
      exact measurable_pi_lambda _ (fun j => (measurable_pi_apply _).comp measurable_fst)

end SCM

/-- Vertices inside the intervention set have empty parent sets after the surgery. -/
theorem doIntervene_clears_parents
    (M : SCM) (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) (i : M.V) (hi : i ∈ X) :
    (M.doIntervene X x).Pa i = ∅ := by
  simp [SCM.doIntervene, hi]
  rfl

/-- Vertices outside the intervention set keep the parent sets they had. -/
theorem doIntervene_preserves_other_parents
    (M : SCM) (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) (i : M.V) (hi : i ∉ X) :
    (M.doIntervene X x).Pa i = M.Pa i := by
  simp [SCM.doIntervene, hi]

end PolicyShift
