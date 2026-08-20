import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.MeanValue

noncomputable section

namespace PolicyShift

open Set

/-- Kullback-Leibler divergence between the Bernoulli laws of mean `p` and mean `q`. -/
def klBin (p q : ℝ) : ℝ :=
  p * Real.log (p / q) + (1 - p) * Real.log ((1 - p) / (1 - q))

/-- The binary divergence vanishes when the two Bernoulli means agree. -/
lemma klBin_self (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    klBin p p = 0 := by
  unfold klBin
  have h1 : p / p = 1 := div_self hp₀.ne'
  have h2 : (1 - p) / (1 - p) = 1 := div_self (by linarith : (1 - p) ≠ 0)
  rw [h1, h2, Real.log_one]
  ring

/-- At `p = 0` the binary divergence collapses to `-log (1 - q)`. -/
lemma klBin_zero_left (q : ℝ) :
    klBin 0 q = -Real.log (1 - q) := by
  unfold klBin
  rw [zero_mul, zero_add, sub_zero]
  have h1 : (1 : ℝ) / (1 - q) = (1 - q)⁻¹ := one_div (1 - q)
  rw [h1, Real.log_inv]
  ring

/-- At `p = 1` the binary divergence collapses to `-log q`. -/
lemma klBin_one_left (q : ℝ) :
    klBin 1 q = -Real.log q := by
  unfold klBin
  rw [sub_self, zero_mul, add_zero, one_mul]
  have h1 : (1 : ℝ) / q = q⁻¹ := one_div q
  rw [h1, Real.log_inv]

/-- Inside the open unit square the binary divergence splits into four logarithmic terms. -/
lemma klBin_expand (p q : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1)
    (hq₀ : 0 < q) (hq₁ : q < 1) :
    klBin p q = p * Real.log p - p * Real.log q
              + (1 - p) * Real.log (1 - p) - (1 - p) * Real.log (1 - q) := by
  unfold klBin
  rw [Real.log_div hp₀.ne' hq₀.ne',
      Real.log_div (by linarith : (1 - p) ≠ 0) (by linarith : (1 - q) ≠ 0)]
  ring

/-- Differentiating the binary divergence in its second argument returns
`(q - p) / (q (1 - q))`. -/
lemma hasDerivAt_klBin_q (p q : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1)
    (hq₀ : 0 < q) (hq₁ : q < 1) :
    HasDerivAt (fun q => klBin p q) ((q - p) / (q * (1 - q))) q := by
  have h_eq : (fun q : ℝ => klBin p q) =ᶠ[nhds q]
              (fun q : ℝ => p * Real.log p - p * Real.log q
                    + (1 - p) * Real.log (1 - p) - (1 - p) * Real.log (1 - q)) := by
    filter_upwards [Ioo_mem_nhds hq₀ hq₁] with x hx
    exact klBin_expand p x hp₀ hp₁ hx.1 hx.2
  refine HasDerivAt.congr_of_eventuallyEq ?_ h_eq
  have h1 : HasDerivAt (fun q => Real.log q) q⁻¹ q := Real.hasDerivAt_log hq₀.ne'
  have h2 : HasDerivAt (fun q => Real.log (1 - q)) (-(1 - q)⁻¹) q := by
    have h_sub : HasDerivAt (fun q : ℝ => 1 - q) (-1 : ℝ) q := by
      simpa using (hasDerivAt_id q).const_sub 1
    have h_log := Real.hasDerivAt_log (by linarith : (1 - q) ≠ 0)
    have hcomp := h_log.comp q h_sub
    simpa only [Function.comp_def, mul_neg_one] using hcomp
  have hd1 : HasDerivAt (fun q => p * Real.log p) 0 q :=
    hasDerivAt_const q _
  have hd2 : HasDerivAt (fun q => p * Real.log q) (p * q⁻¹) q := h1.const_mul p
  have hd3 : HasDerivAt (fun q => (1 - p) * Real.log (1 - p)) 0 q :=
    hasDerivAt_const q _
  have hd4 : HasDerivAt (fun q => (1 - p) * Real.log (1 - q))
      ((1 - p) * (-(1 - q)⁻¹)) q := h2.const_mul (1 - p)
  have hsum := ((hd1.sub hd2).add hd3).sub hd4
  have hq_ne : q ≠ 0 := hq₀.ne'
  have hq1_ne : (1 - q) ≠ 0 := by linarith
  refine hsum.congr_deriv ?_
  field_simp
  ring

/-- The squared deviation `(p - q)²` has derivative `-2 (p - q)` in `q`. -/
lemma hasDerivAt_sub_sq (p q : ℝ) :
    HasDerivAt (fun q : ℝ => (p - q)^2) (-2 * (p - q)) q := by
  have h1 : HasDerivAt (fun q : ℝ => p - q) (-1 : ℝ) q := by
    simpa using (hasDerivAt_id q).const_sub p
  have h2 := h1.fun_pow 2
  refine h2.congr_deriv ?_
  ring

/-- The Pinsker gap `klBin p q - 2 (p - q)²` has derivative `(q - p) (1 - 2q)² / (q (1 - q))`. -/
lemma hasDerivAt_g (p q : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1)
    (hq₀ : 0 < q) (hq₁ : q < 1) :
    HasDerivAt
      (fun q => klBin p q - 2 * (p - q)^2)
      ((q - p) * (1 - 2*q)^2 / (q * (1 - q)))
      q := by
  have h1 := hasDerivAt_klBin_q p q hp₀ hp₁ hq₀ hq₁
  have h2 : HasDerivAt (fun q : ℝ => 2 * (p - q)^2) (2 * (-2 * (p - q))) q :=
    (hasDerivAt_sub_sq p q).const_mul 2
  have h3 := h1.sub h2
  have hq_ne : q ≠ 0 := hq₀.ne'
  have hq1_ne : (1 - q) ≠ 0 := by linarith
  refine h3.congr_deriv ?_
  field_simp
  ring

/-- The factor `(1 - 2q)² / (q (1 - q))` is nonnegative across the open unit interval. -/
lemma deriv_factor_nonneg (q : ℝ) (hq₀ : 0 < q) (hq₁ : q < 1) :
    0 ≤ (1 - 2*q)^2 / (q * (1 - q)) := by
  apply div_nonneg (sq_nonneg _)
  exact (mul_pos hq₀ (by linarith : (0 : ℝ) < 1 - q)).le

/-- Above `p` the derivative of the Pinsker gap is nonnegative. -/
lemma deriv_g_nonneg_of_ge (p q : ℝ) (hpq : p ≤ q) (hq₀ : 0 < q) (hq₁ : q < 1) :
    0 ≤ (q - p) * (1 - 2*q)^2 / (q * (1 - q)) := by
  have hf : 0 ≤ (1 - 2*q)^2 / (q * (1 - q)) := deriv_factor_nonneg q hq₀ hq₁
  have hqp : 0 ≤ q - p := by linarith
  rw [mul_div_assoc]
  exact mul_nonneg hqp hf

/-- Below `p` the derivative of the Pinsker gap is nonpositive. -/
lemma deriv_g_nonpos_of_le (p q : ℝ) (hqp : q ≤ p) (hq₀ : 0 < q) (hq₁ : q < 1) :
    (q - p) * (1 - 2*q)^2 / (q * (1 - q)) ≤ 0 := by
  have hf : 0 ≤ (1 - 2*q)^2 / (q * (1 - q)) := deriv_factor_nonneg q hq₀ hq₁
  have hqp' : q - p ≤ 0 := by linarith
  rw [mul_div_assoc]
  exact mul_nonpos_of_nonpos_of_nonneg hqp' hf

/-- The binary divergence is continuous in its second argument on `[p, 1)`. -/
private lemma continuousOn_klBin_Ico (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    ContinuousOn (fun q => klBin p q) (Set.Ico p 1) := by
  intro q hq
  have hq₀ : 0 < q := lt_of_lt_of_le hp₀ hq.1
  have hq₁ : q < 1 := hq.2
  exact (hasDerivAt_klBin_q p q hp₀ hp₁ hq₀ hq₁).continuousAt.continuousWithinAt

/-- The binary divergence is continuous in its second argument on `(0, p]`. -/
private lemma continuousOn_klBin_Ioc (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    ContinuousOn (fun q => klBin p q) (Set.Ioc 0 p) := by
  intro q hq
  have hq₀ : 0 < q := hq.1
  have hq₁ : q < 1 := lt_of_le_of_lt hq.2 hp₁
  exact (hasDerivAt_klBin_q p q hp₀ hp₁ hq₀ hq₁).continuousAt.continuousWithinAt

/-- The squared deviation is continuous on every set. -/
private lemma continuousOn_sub_sq (p : ℝ) (s : Set ℝ) :
    ContinuousOn (fun q : ℝ => (p - q)^2) s :=
  (Continuous.continuousOn (by continuity))

/-- The Pinsker gap is continuous on `[p, 1)`. -/
private lemma continuousOn_g_Ico (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    ContinuousOn (fun q => klBin p q - 2 * (p - q)^2) (Set.Ico p 1) := by
  apply ContinuousOn.sub (continuousOn_klBin_Ico p hp₀ hp₁)
  exact continuousOn_const.mul (continuousOn_sub_sq p _)

/-- The Pinsker gap is continuous on `(0, p]`. -/
private lemma continuousOn_g_Ioc (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    ContinuousOn (fun q => klBin p q - 2 * (p - q)^2) (Set.Ioc 0 p) := by
  apply ContinuousOn.sub (continuousOn_klBin_Ioc p hp₀ hp₁)
  exact continuousOn_const.mul (continuousOn_sub_sq p _)

/-- The Pinsker gap increases on `[p, 1)`. -/
lemma monotoneOn_g (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    MonotoneOn (fun q => klBin p q - 2 * (p - q)^2) (Set.Ico p 1) := by
  apply monotoneOn_of_deriv_nonneg (convex_Ico p 1)
  · exact continuousOn_g_Ico p hp₀ hp₁
  · rw [interior_Ico]
    intro q hq
    have hq₀ : 0 < q := lt_trans hp₀ hq.1
    exact (hasDerivAt_g p q hp₀ hp₁ hq₀ hq.2).differentiableAt.differentiableWithinAt
  · rw [interior_Ico]
    intro q hq
    have hq₀ : 0 < q := lt_trans hp₀ hq.1
    rw [(hasDerivAt_g p q hp₀ hp₁ hq₀ hq.2).deriv]
    exact deriv_g_nonneg_of_ge p q hq.1.le hq₀ hq.2

/-- The Pinsker gap decreases on `(0, p]`. -/
lemma antitoneOn_g (p : ℝ) (hp₀ : 0 < p) (hp₁ : p < 1) :
    AntitoneOn (fun q => klBin p q - 2 * (p - q)^2) (Set.Ioc 0 p) := by
  apply antitoneOn_of_deriv_nonpos (convex_Ioc 0 p)
  · exact continuousOn_g_Ioc p hp₀ hp₁
  · rw [interior_Ioc]
    intro q hq
    have hq₁ : q < 1 := lt_trans hq.2 hp₁
    exact (hasDerivAt_g p q hp₀ hp₁ hq.1 hq₁).differentiableAt.differentiableWithinAt
  · rw [interior_Ioc]
    intro q hq
    have hq₁ : q < 1 := lt_trans hq.2 hp₁
    rw [(hasDerivAt_g p q hp₀ hp₁ hq.1 hq₁).deriv]
    exact deriv_g_nonpos_of_le p q hq.2.le hq.1 hq₁

/-- The boundary gap `-log (1 - q) - 2q²` has derivative `(2q - 1)² / (1 - q)`. -/
private lemma hasDerivAt_h_zero (q : ℝ) (hq₁ : q < 1) :
    HasDerivAt (fun q : ℝ => -Real.log (1 - q) - 2 * q^2) ((2*q - 1)^2 / (1 - q)) q := by
  have h1q_ne : (1 - q) ≠ 0 := by linarith
  have h_sub : HasDerivAt (fun q : ℝ => 1 - q) (-1 : ℝ) q := by
    simpa using (hasDerivAt_id q).const_sub 1
  have h_log := Real.hasDerivAt_log h1q_ne
  have hlog1q := h_log.comp q h_sub
  have hlog1q' : HasDerivAt (fun q : ℝ => Real.log (1 - q)) (-(1 - q)⁻¹) q := by
    refine hlog1q.congr_deriv ?_
    ring
  have hneg_log : HasDerivAt (fun q : ℝ => -Real.log (1 - q)) ((1 - q)⁻¹) q := by
    refine hlog1q'.neg.congr_deriv ?_
    ring
  have hsq : HasDerivAt (fun q : ℝ => 2 * q^2) (4 * q) q := by
    have h_pow := hasDerivAt_pow 2 q
    have h_mul := h_pow.const_mul 2
    refine h_mul.congr_deriv ?_
    ring
  have hsum := hneg_log.sub hsq
  refine hsum.congr_deriv ?_
  field_simp
  ring

/-- The boundary gap `-log (1 - q) - 2q²` increases on `[0, 1)`. -/
private lemma monotoneOn_h_zero : MonotoneOn (fun q : ℝ => -Real.log (1 - q) - 2 * q^2)
    (Set.Ico (0 : ℝ) 1) := by
  apply monotoneOn_of_deriv_nonneg (convex_Ico 0 1)
  · intro q hq
    have hq₁ : q < 1 := hq.2
    exact (hasDerivAt_h_zero q hq₁).continuousAt.continuousWithinAt
  · rw [interior_Ico]
    intro q hq
    exact (hasDerivAt_h_zero q hq.2).differentiableAt.differentiableWithinAt
  · rw [interior_Ico]
    intro q hq
    rw [(hasDerivAt_h_zero q hq.2).deriv]
    apply div_nonneg (sq_nonneg _)
    linarith [hq.2]

/-- `2 q² ≤ -log (1 - q)` for `q` in `[0, 1)`. -/
lemma two_sq_le_neg_log_one_sub (q : ℝ) (hq₀ : 0 ≤ q) (hq₁ : q < 1) :
    2 * q^2 ≤ -Real.log (1 - q) := by
  have h0_mem : (0 : ℝ) ∈ Set.Ico (0 : ℝ) 1 := ⟨le_refl 0, one_pos⟩
  have hq_mem : q ∈ Set.Ico (0 : ℝ) 1 := ⟨hq₀, hq₁⟩
  have hmono := monotoneOn_h_zero h0_mem hq_mem hq₀
  simp at hmono
  linarith

/-- `2 (1 - q)² ≤ -log q` for `q` in `(0, 1]`. -/
lemma two_sq_le_neg_log (q : ℝ) (hq₀ : 0 < q) (hq₁ : q ≤ 1) :
    2 * (1 - q)^2 ≤ -Real.log q := by
  have hr₀ : (0 : ℝ) ≤ 1 - q := by linarith
  have hr₁ : (1 - q) < 1 := by linarith
  have := two_sq_le_neg_log_one_sub (1 - q) hr₀ hr₁
  have h_sub : (1 : ℝ) - (1 - q) = q := by ring
  rw [h_sub] at this
  exact this

/-- Binary Pinsker inequality: `2 (p - q)² ≤ klBin p q` with the sharp constant `2`. -/
theorem binary_pinsker (p q : ℝ) (hp₀ : 0 ≤ p) (hp₁ : p ≤ 1)
    (hq₀ : 0 < q) (hq₁ : q < 1) :
    2 * (p - q)^2 ≤ klBin p q := by
  suffices hg : 0 ≤ klBin p q - 2 * (p - q)^2 by linarith
  rcases eq_or_lt_of_le hp₀ with hp_eq | hp_pos
  · rw [← hp_eq]
    rw [klBin_zero_left q]
    have h := two_sq_le_neg_log_one_sub q hq₀.le hq₁
    have h_sq : (0 - q)^2 = q^2 := by ring
    rw [h_sq]
    linarith
  rcases eq_or_lt_of_le hp₁ with hp_eq | hp_lt
  · rw [hp_eq]
    rw [klBin_one_left q]
    have h := two_sq_le_neg_log q hq₀ hq₁.le
    have h_sq : (1 - q)^2 = (1 - q)^2 := rfl
    linarith
  rcases le_or_gt p q with hpq | hpq
  · have hmono := monotoneOn_g p hp_pos hp_lt
    have hp_mem : p ∈ Set.Ico p 1 := ⟨le_refl p, hp_lt⟩
    have hq_mem : q ∈ Set.Ico p 1 := ⟨hpq, hq₁⟩
    have h_ge := hmono hp_mem hq_mem hpq
    have h_self : klBin p p - 2 * (p - p)^2 = 0 := by
      rw [klBin_self p hp_pos hp_lt]; ring
    linarith
  · have hanti := antitoneOn_g p hp_pos hp_lt
    have hp_mem : p ∈ Set.Ioc 0 p := ⟨hp_pos, le_refl p⟩
    have hq_mem : q ∈ Set.Ioc 0 p := ⟨hq₀, hpq.le⟩
    have h_ge := hanti hq_mem hp_mem hpq.le
    have h_self : klBin p p - 2 * (p - p)^2 = 0 := by
      rw [klBin_self p hp_pos hp_lt]; ring
    linarith

end PolicyShift

end
