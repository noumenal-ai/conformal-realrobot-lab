import FiniteExpectation
import BinaryPinsker
import OddsDifference
import DoInterventionParents
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Tactic

noncomputable section

namespace PolicyShift

open scoped BigOperators
open Finset Real

/-- Source-weighted density-ratio error equals `1/ρ` times the mixture mean of
`|η - h| / (1 - h)`. -/
theorem finite_posterior_ratio_identity
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ) (ρ : ℝ)
    (hρ0 : 0 < ρ) (hρ1 : ρ < 1)
    (hη1 : ∀ i, η i < 1) (hh1 : ∀ i, h i < 1) :
    (∑ i : ι, sourceMass M η ρ i *
      |ratioFromPosterior ρ (η i) - ratioFromPosterior ρ (h i)|)
      = (1 / ρ) * expectation M (fun i => |η i - h i| / (1 - h i)) := by
  unfold expectation
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro i hi
  have hρne : ρ ≠ 0 := ne_of_gt hρ0
  have h1ρpos : 0 < 1 - ρ := sub_pos.mpr hρ1
  have h1ηpos : 0 < 1 - η i := sub_pos.mpr (hη1 i)
  have h1hpos : 0 < 1 - h i := sub_pos.mpr (hh1 i)
  have h1ρne : 1 - ρ ≠ 0 := ne_of_gt h1ρpos
  have h1ηne : 1 - η i ≠ 0 := ne_of_gt h1ηpos
  have h1hne : 1 - h i ≠ 0 := ne_of_gt h1hpos
  unfold sourceMass ratioFromPosterior
  rw [← mul_sub, odds_sub_odds (η i) (h i) (ne_of_lt (hη1 i)) (ne_of_lt (hh1 i))]
  rw [abs_mul, abs_div, abs_div, abs_mul]
  rw [abs_of_pos h1ρpos, abs_of_pos hρ0, abs_of_pos h1ηpos, abs_of_pos h1hpos]
  field_simp [hρne, h1ρne, h1ηne, h1hne]

/-- Pinsker in absolute-error form: `|p - q| ≤ sqrt (klBin p q / 2)`. -/
theorem abs_sub_le_sqrt_klBin
    (p q : ℝ) (hp0 : 0 ≤ p) (hp1 : p ≤ 1) (hq0 : 0 < q) (hq1 : q < 1) :
    |p - q| ≤ Real.sqrt (klBin p q / 2) := by
  have hb := binary_pinsker p q hp0 hp1 hq0 hq1
  rw [← Real.sqrt_sq_eq_abs (p - q)]
  apply Real.sqrt_le_sqrt
  nlinarith

/-- The mean absolute posterior error is at most the square root of half the mean binary
divergence. -/
theorem finite_mean_abs_le_sqrt_mean_kl
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ)
    (hη0 : ∀ i, 0 ≤ η i) (hη1 : ∀ i, η i ≤ 1)
    (hh0 : ∀ i, 0 < h i) (hh1 : ∀ i, h i < 1) :
    expectation M (fun i => |η i - h i|)
      ≤ Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2) := by
  have hkl : ∀ i, 0 ≤ klBin (η i) (h i) / 2 := by
    intro i
    have hb := binary_pinsker (η i) (h i)
      (hη0 i) (hη1 i) (hh0 i) (hh1 i)
    nlinarith [sq_nonneg (η i - h i)]
  have hpoint : expectation M (fun i => |η i - h i|)
      ≤ ∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2) := by
    unfold expectation
    apply Finset.sum_le_sum
    intro i hi
    exact mul_le_mul_of_nonneg_left
      (abs_sub_le_sqrt_klBin (η i) (h i) (hη0 i) (hη1 i) (hh0 i) (hh1 i))
      (M.prob_nonneg i)
  have hCS := Finset.sum_mul_sq_le_sq_mul_sq Finset.univ
    (fun i : ι => Real.sqrt (M.prob i))
    (fun i : ι => Real.sqrt (M.prob i) * Real.sqrt (klBin (η i) (h i) / 2))
  have hCS' :
      (∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2)) ^ 2
        ≤ expectation M (fun i => klBin (η i) (h i)) / 2 := by
    calc
      (∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2)) ^ 2
          = (∑ i : ι, Real.sqrt (M.prob i) *
              (Real.sqrt (M.prob i) * Real.sqrt (klBin (η i) (h i) / 2))) ^ 2 := by
              congr 1
              apply Finset.sum_congr rfl
              intro i hi
              calc
                M.prob i * Real.sqrt (klBin (η i) (h i) / 2)
                    = Real.sqrt (M.prob i) ^ 2 *
                      Real.sqrt (klBin (η i) (h i) / 2) := by
                        rw [Real.sq_sqrt (M.prob_nonneg i)]
                _ = Real.sqrt (M.prob i) *
                    (Real.sqrt (M.prob i) * Real.sqrt (klBin (η i) (h i) / 2)) := by ring
      _ ≤ (∑ i : ι, Real.sqrt (M.prob i) ^ 2) *
          ∑ i : ι, (Real.sqrt (M.prob i) *
            Real.sqrt (klBin (η i) (h i) / 2)) ^ 2 := hCS
      _ = expectation M (fun i => klBin (η i) (h i)) / 2 := by
          rw [Finset.sum_congr rfl (fun i _ => Real.sq_sqrt (M.prob_nonneg i)), M.prob_sum_one]
          simp_rw [mul_pow, Real.sq_sqrt (M.prob_nonneg _), Real.sq_sqrt (hkl _)]
          unfold expectation
          rw [one_mul, Finset.sum_div]
          apply Finset.sum_congr rfl
          intro i hi
          ring
  have hleft0 : 0 ≤ expectation M (fun i => |η i - h i|) := by
    unfold expectation
    exact Finset.sum_nonneg (fun i _ => mul_nonneg (M.prob_nonneg i) (abs_nonneg _))
  have hmiddle0 : 0 ≤ ∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2) :=
    Finset.sum_nonneg (fun i _ => mul_nonneg (M.prob_nonneg i) (Real.sqrt_nonneg _))
  rw [← abs_of_nonneg hleft0,
    ← Real.sqrt_sq_eq_abs (expectation M (fun i => |η i - h i|))]
  apply Real.sqrt_le_sqrt
  have hsquares :
      (expectation M (fun i => |η i - h i|)) ^ 2
        ≤ (∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2)) ^ 2 := by
    nlinarith
  exact le_trans hsquares hCS'

set_option linter.unusedVariables false in
/-- Density-ratio `L¹` error is at most `1 / (ρ γ)` times the square root of half the mean
classifier divergence. -/
theorem domain_classifier_regret_to_ratio_l1
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ) (ρ γ : ℝ)
    (hρ0 : 0 < ρ) (hρ1 : ρ < 1)
    (hγ0 : 0 < γ) (hγ1 : γ < 1)
    (hη0 : ∀ i, 0 ≤ η i) (hη1 : ∀ i, η i < 1)
    (hh0 : ∀ i, 0 < h i) (hhγ : ∀ i, h i ≤ 1 - γ) :
    (∑ i : ι, sourceMass M η ρ i *
      |ratioFromPosterior ρ (η i) - ratioFromPosterior ρ (h i)|)
      ≤ (1 / (ρ * γ)) *
        Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2) := by
  have hη1le : ∀ i, η i ≤ 1 := fun i => (hη1 i).le
  have hh1 : ∀ i, h i < 1 := by
    intro i
    linarith [hhγ i, hγ0]
  rw [finite_posterior_ratio_identity M η h ρ hρ0 hρ1 hη1 hh1]
  have hfrac : expectation M (fun i => |η i - h i| / (1 - h i))
      ≤ (1 / γ) * expectation M (fun i => |η i - h i|) := by
    unfold expectation
    rw [Finset.mul_sum]
    apply Finset.sum_le_sum
    intro i hi
    have hden : γ ≤ 1 - h i := by linarith [hhγ i]
    have hdiv : |η i - h i| / (1 - h i) ≤ |η i - h i| / γ :=
      div_le_div_of_nonneg_left (abs_nonneg _) hγ0 hden
    calc
      M.prob i * (|η i - h i| / (1 - h i))
          ≤ M.prob i * (|η i - h i| / γ) :=
            mul_le_mul_of_nonneg_left hdiv (M.prob_nonneg i)
      _ = (1 / γ) * (M.prob i * |η i - h i|) := by ring
  have hmean := finite_mean_abs_le_sqrt_mean_kl M η h hη0 hη1le hh0 hh1
  calc
    (1 / ρ) * expectation M (fun i => |η i - h i| / (1 - h i))
        ≤ (1 / ρ) * ((1 / γ) * expectation M (fun i => |η i - h i|)) :=
          mul_le_mul_of_nonneg_left hfrac (by positivity)
    _ ≤ (1 / ρ) * ((1 / γ) *
        Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2)) := by
          gcongr
    _ = (1 / (ρ * γ)) *
        Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2) := by
          field_simp [ne_of_gt hρ0, ne_of_gt hγ0]

/-- At a balanced mixture the same bound reads `sqrt (2 · mean divergence) / γ`. -/
theorem balanced_domain_classifier_regret_to_ratio_l1
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ) (γ : ℝ)
    (hγ0 : 0 < γ) (hγ1 : γ < 1)
    (hη0 : ∀ i, 0 ≤ η i) (hη1 : ∀ i, η i < 1)
    (hh0 : ∀ i, 0 < h i) (hhγ : ∀ i, h i ≤ 1 - γ) :
    (∑ i : ι, sourceMass M η (1 / 2) i *
      |ratioFromPosterior (1 / 2) (η i) - ratioFromPosterior (1 / 2) (h i)|)
      ≤ (Real.sqrt (2 * expectation M (fun i => klBin (η i) (h i)))) / γ := by
  have hbase := domain_classifier_regret_to_ratio_l1 M η h (1 / 2) γ
    (by norm_num) (by norm_num) hγ0 hγ1 hη0 hη1 hh0 hhγ
  have hE : 0 ≤ expectation M (fun i => klBin (η i) (h i)) := by
    unfold expectation
    apply Finset.sum_nonneg
    intro i hi
    have hb := binary_pinsker (η i) (h i)
      (hη0 i) (hη1 i).le (hh0 i) (by linarith [hhγ i, hγ0])
    exact mul_nonneg (M.prob_nonneg i) (by nlinarith [sq_nonneg (η i - h i)])
  have hsqrt : 2 * Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2)
      = Real.sqrt (2 * expectation M (fun i => klBin (η i) (h i))) := by
    have ha := Real.sq_sqrt (div_nonneg hE (by norm_num : (0 : ℝ) ≤ 2))
    have hb := Real.sq_sqrt (mul_nonneg (by norm_num : (0 : ℝ) ≤ 2) hE)
    have ha0 := Real.sqrt_nonneg (expectation M (fun i => klBin (η i) (h i)) / 2)
    have hb0 := Real.sqrt_nonneg (2 * expectation M (fun i => klBin (η i) (h i)))
    nlinarith
  calc
    (∑ i : ι, sourceMass M η (1 / 2) i *
      |ratioFromPosterior (1 / 2) (η i) - ratioFromPosterior (1 / 2) (h i)|)
        ≤ (1 / ((1 / 2) * γ)) *
          Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2) := hbase
    _ = (2 * Real.sqrt (expectation M (fun i => klBin (η i) (h i)) / 2)) / γ := by
          field_simp [ne_of_gt hγ0]
    _ = Real.sqrt (2 * expectation M (fun i => klBin (η i) (h i))) / γ := by rw [hsqrt]

/-- A coverage lower bound stated with the ratio error survives replacing that error by any
upper bound for it. -/
theorem classifier_regret_coverage_composition
    (coverage α ratioError bound : ℝ)
    (htransfer : 1 - α - ratioError ≤ coverage)
    (hratio : ratioError ≤ bound) :
    1 - α - bound ≤ coverage := by
  linarith

/-- Under a shared state law and transition kernel, propensity reweighting is an exact change
of measure. -/
theorem common_state_propensity_identity
    {S A Y : Type*} [Fintype S] [Fintype A] [Fintype Y]
    (μ : S → ℝ) (πb πt : S → A → ℝ) (K : S → A → Y → ℝ)
    (f : S → A → Y → ℝ)
    (hpos : ∀ s a, 0 < πb s a) :
    (∑ s : S, ∑ a : A, ∑ y : Y, μ s * πt s a * K s a y * f s a y)
      = ∑ s : S, ∑ a : A, ∑ y : Y,
          μ s * πb s a * K s a y * ((πt s a / πb s a) * f s a y) := by
  apply Finset.sum_congr rfl
  intro s hs
  apply Finset.sum_congr rfl
  intro a ha
  apply Finset.sum_congr rfl
  intro y hy
  have hne : πb s a ≠ 0 := ne_of_gt (hpos s a)
  field_simp [hne]

end PolicyShift

end
