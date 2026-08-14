import ConformalCounterfactuals.DomainClassifier

namespace ConformalCounterfactuals

/-- Pure arithmetic composition of the existing approximate-weight conformal transfer theorem
with the new domain-classifier ratio-error certificate. -/
theorem classifier_regret_coverage_composition
    (coverage α ratioError certificate : ℝ)
    (htransfer : 1 - α - ratioError ≤ coverage)
    (hratio : ratioError ≤ certificate) :
    1 - α - certificate ≤ coverage := by
  linarith

end ConformalCounterfactuals
