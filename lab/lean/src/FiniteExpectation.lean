import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fintype.BigOperators

namespace PolicyShift

/-- A real-valued probability mass function on a finite index type. -/
structure FintypePMF (α : Type*) [Fintype α] where
  /-- Weight assigned to each index. -/
  prob : α → ℝ
  /-- Weights are nonnegative. -/
  prob_nonneg : ∀ a, 0 ≤ prob a
  /-- Weights sum to one. -/
  prob_sum_one : ∑ a : α, prob a = 1

noncomputable section

/-- The mean of a real-valued function against a finite probability mass function. -/
def expectation {α : Type*} [Fintype α]
    (p : FintypePMF α) (f : α → ℝ) : ℝ :=
  ∑ a : α, p.prob a * f a

end

end PolicyShift
