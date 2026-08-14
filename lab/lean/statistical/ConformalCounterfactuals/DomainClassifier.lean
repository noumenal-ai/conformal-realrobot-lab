import ZPM.InformationTheory.Pinsker.Binary
import ZPM.Probability.FintypePMF.Expectation
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Tactic

/-!
Finite-support formalization of the domain-classifier regret bound used by the real-robot
experiment. The support is the indexed finite pool of observed transitions.
-/

noncomputable section

namespace ConformalCounterfactuals

open scoped BigOperators
open Finset Real InformationTheory ProbabilityTheory ProbabilityTheory.FintypePMF

/-- Posterior odds. -/
def odds (u : ℝ) : ℝ := u / (1 - u)

/-- Density ratio induced by a domain posterior with target-domain prior `ρ`. -/
def ratioFromPosterior (ρ u : ℝ) : ℝ := ((1 - ρ) / ρ) * odds u

/-- Source mass written relative to the balanced-domain mixture mass. -/
def sourceMass {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η : ι → ℝ) (ρ : ℝ) (i : ι) : ℝ :=
  M.prob i * (1 - η i) / (1 - ρ)

/-- Exact algebraic difference of two odds. -/
theorem odds_sub_odds (u v : ℝ) (hu : u ≠ 1) (hv : v ≠ 1) :
    odds u - odds v = (u - v) / ((1 - u) * (1 - v)) := by
  -- BEGIN AUTOFORMALIZE_ONLY odds_sub_odds
  unfold odds
  have hu0 : 1 - u ≠ 0 := sub_ne_zero.mpr hu.symm
  have hv0 : 1 - v ≠ 0 := sub_ne_zero.mpr hv.symm
  field_simp [hu0, hv0]
  <;> ring
  -- END AUTOFORMALIZE_ONLY odds_sub_odds

/-- Exact cancellation converting posterior error under the mixture to ratio error under P. -/
theorem finite_posterior_ratio_identity
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ) (ρ : ℝ)
    (hρ0 : 0 < ρ) (hρ1 : ρ < 1)
    (hη1 : ∀ i, η i < 1) (hh1 : ∀ i, h i < 1) :
    (∑ i : ι, sourceMass M η ρ i *
      |ratioFromPosterior ρ (η i) - ratioFromPosterior ρ (h i)|)
      = (1 / ρ) * trueExpectation M (fun i => |η i - h i| / (1 - h i)) := by
  -- BEGIN AUTOFORMALIZE_ONLY finite_posterior_ratio_identity
  unfold trueExpectation
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
  <;> ring
  -- END AUTOFORMALIZE_ONLY finite_posterior_ratio_identity

/-- Binary Pinsker rewritten as an absolute-error bound. Uses the supplied theorem
`InformationTheory.binary_pinsker` with its sharp constant 2. -/
theorem abs_sub_le_sqrt_klBin
    (p q : ℝ) (hp0 : 0 ≤ p) (hp1 : p ≤ 1) (hq0 : 0 < q) (hq1 : q < 1) :
    |p - q| ≤ Real.sqrt (klBin p q / 2) := by
  -- BEGIN AUTOFORMALIZE_ONLY abs_sub_le_sqrt_klBin
  have hb := InformationTheory.binary_pinsker p q hp0 hp1 hq0 hq1
  rw [← Real.sqrt_sq_eq_abs (p - q)]
  apply Real.sqrt_le_sqrt
  nlinarith
  -- END AUTOFORMALIZE_ONLY abs_sub_le_sqrt_klBin

/-- Finite weighted Cauchy/Jensen step. -/
theorem finite_mean_abs_le_sqrt_mean_kl
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ)
    (hη0 : ∀ i, 0 ≤ η i) (hη1 : ∀ i, η i ≤ 1)
    (hh0 : ∀ i, 0 < h i) (hh1 : ∀ i, h i < 1) :
    trueExpectation M (fun i => |η i - h i|)
      ≤ Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2) := by
  -- BEGIN AUTOFORMALIZE_ONLY finite_mean_abs_le_sqrt_mean_kl
  have hkl : ∀ i, 0 ≤ klBin (η i) (h i) / 2 := by
    intro i
    have hb := InformationTheory.binary_pinsker (η i) (h i)
      (hη0 i) (hη1 i) (hh0 i) (hh1 i)
    nlinarith [sq_nonneg (η i - h i)]
  have hpoint : trueExpectation M (fun i => |η i - h i|)
      ≤ ∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2) := by
    unfold trueExpectation
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
        ≤ trueExpectation M (fun i => klBin (η i) (h i)) / 2 := by
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
      _ = trueExpectation M (fun i => klBin (η i) (h i)) / 2 := by
          rw [Finset.sum_congr rfl (fun i _ => Real.sq_sqrt (M.prob_nonneg i)), M.prob_sum_one]
          simp_rw [mul_pow, Real.sq_sqrt (M.prob_nonneg _), Real.sq_sqrt (hkl _)]
          unfold trueExpectation
          rw [one_mul, Finset.sum_div]
          apply Finset.sum_congr rfl
          intro i hi
          ring
  have hleft0 : 0 ≤ trueExpectation M (fun i => |η i - h i|) := by
    unfold trueExpectation
    exact Finset.sum_nonneg (fun i _ => mul_nonneg (M.prob_nonneg i) (abs_nonneg _))
  have hmiddle0 : 0 ≤ ∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2) :=
    Finset.sum_nonneg (fun i _ => mul_nonneg (M.prob_nonneg i) (Real.sqrt_nonneg _))
  rw [← abs_of_nonneg hleft0,
    ← Real.sqrt_sq_eq_abs (trueExpectation M (fun i => |η i - h i|))]
  apply Real.sqrt_le_sqrt
  have hsquares :
      (trueExpectation M (fun i => |η i - h i|)) ^ 2
        ≤ (∑ i : ι, M.prob i * Real.sqrt (klBin (η i) (h i) / 2)) ^ 2 := by
    nlinarith
  exact le_trans hsquares hCS'
  -- END AUTOFORMALIZE_ONLY finite_mean_abs_le_sqrt_mean_kl

/-- The requested finite-pool theorem with the exact constant `1 / (ρ γ)`. -/
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
        Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2) := by
  -- BEGIN AUTOFORMALIZE_ONLY domain_classifier_regret_to_ratio_l1
  have hη1le : ∀ i, η i ≤ 1 := fun i => (hη1 i).le
  have hh1 : ∀ i, h i < 1 := by
    intro i
    linarith [hhγ i, hγ0]
  rw [finite_posterior_ratio_identity M η h ρ hρ0 hρ1 hη1 hh1]
  have hfrac : trueExpectation M (fun i => |η i - h i| / (1 - h i))
      ≤ (1 / γ) * trueExpectation M (fun i => |η i - h i|) := by
    unfold trueExpectation
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
    (1 / ρ) * trueExpectation M (fun i => |η i - h i| / (1 - h i))
        ≤ (1 / ρ) * ((1 / γ) * trueExpectation M (fun i => |η i - h i|)) :=
          mul_le_mul_of_nonneg_left hfrac (by positivity)
    _ ≤ (1 / ρ) * ((1 / γ) *
        Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2)) := by
          gcongr
    _ = (1 / (ρ * γ)) *
        Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2) := by
          field_simp [ne_of_gt hρ0, ne_of_gt hγ0]
          <;> ring
  -- END AUTOFORMALIZE_ONLY domain_classifier_regret_to_ratio_l1

/-- Balanced-domain specialization (`ρ = 1/2`). -/
theorem balanced_domain_classifier_regret_to_ratio_l1
    {ι : Type*} [Fintype ι]
    (M : FintypePMF ι) (η h : ι → ℝ) (γ : ℝ)
    (hγ0 : 0 < γ) (hγ1 : γ < 1)
    (hη0 : ∀ i, 0 ≤ η i) (hη1 : ∀ i, η i < 1)
    (hh0 : ∀ i, 0 < h i) (hhγ : ∀ i, h i ≤ 1 - γ) :
    (∑ i : ι, sourceMass M η (1 / 2) i *
      |ratioFromPosterior (1 / 2) (η i) - ratioFromPosterior (1 / 2) (h i)|)
      ≤ (Real.sqrt (2 * trueExpectation M (fun i => klBin (η i) (h i)))) / γ := by
  -- BEGIN AUTOFORMALIZE_ONLY balanced_domain_classifier_regret_to_ratio_l1
  have hbase := domain_classifier_regret_to_ratio_l1 M η h (1 / 2) γ
    (by norm_num) (by norm_num) hγ0 hγ1 hη0 hη1 hh0 hhγ
  have hE : 0 ≤ trueExpectation M (fun i => klBin (η i) (h i)) := by
    unfold trueExpectation
    apply Finset.sum_nonneg
    intro i hi
    have hb := InformationTheory.binary_pinsker (η i) (h i)
      (hη0 i) (hη1 i).le (hh0 i) (by linarith [hhγ i, hγ0])
    exact mul_nonneg (M.prob_nonneg i) (by nlinarith [sq_nonneg (η i - h i)])
  have hsqrt : 2 * Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2)
      = Real.sqrt (2 * trueExpectation M (fun i => klBin (η i) (h i))) := by
    have ha := Real.sq_sqrt (div_nonneg hE (by norm_num : (0 : ℝ) ≤ 2))
    have hb := Real.sq_sqrt (mul_nonneg (by norm_num : (0 : ℝ) ≤ 2) hE)
    have ha0 := Real.sqrt_nonneg (trueExpectation M (fun i => klBin (η i) (h i)) / 2)
    have hb0 := Real.sqrt_nonneg (2 * trueExpectation M (fun i => klBin (η i) (h i)))
    nlinarith
  calc
    (∑ i : ι, sourceMass M η (1 / 2) i *
      |ratioFromPosterior (1 / 2) (η i) - ratioFromPosterior (1 / 2) (h i)|)
        ≤ (1 / ((1 / 2) * γ)) *
          Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2) := hbase
    _ = (2 * Real.sqrt (trueExpectation M (fun i => klBin (η i) (h i)) / 2)) / γ := by
          field_simp [ne_of_gt hγ0]
          <;> ring
    _ = Real.sqrt (2 * trueExpectation M (fun i => klBin (η i) (h i))) / γ := by rw [hsqrt]
  -- END AUTOFORMALIZE_ONLY balanced_domain_classifier_regret_to_ratio_l1

end ConformalCounterfactuals
