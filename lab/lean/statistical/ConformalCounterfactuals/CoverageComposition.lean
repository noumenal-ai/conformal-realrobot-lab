import ConformalCounterfactuals.DomainClassifier

namespace ConformalCounterfactuals

/-- Pure arithmetic composition of the existing approximate-weight conformal transfer theorem
with the new domain-classifier ratio-error bound. -/
theorem classifier_regret_coverage_composition
    (coverage α ratioError bound : ℝ)
    (htransfer : 1 - α - ratioError ≤ coverage)
    (hratio : ratioError ≤ bound) :
    1 - α - bound ≤ coverage := by
  linarith

end ConformalCounterfactuals
