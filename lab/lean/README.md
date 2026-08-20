# Machine-checked results for calibration under policy shift

A self-contained Lean 4 package containing the formal proofs accompanying the preprint
*Calibrated for Which Policy? Conformal Uncertainty for Fixed World Models Under
Intervention* (Mittal and Gupta, 2026). It establishes, over finite support:

- the exact identity converting domain-classifier posterior error into density-ratio
  `L¹` error under the source law, with a `1/ρ` factor;
- the binary Pinsker inequality with the sharp constant `2`, and the weighted
  Cauchy–Schwarz step that lifts it from pointwise to mean form;
- the density-ratio error bound `1/(ργ) · sqrt(mean binary divergence / 2)`, and its
  balanced-mixture specialization `sqrt(2 · mean divergence)/γ`;
- the arithmetic composition that carries a coverage lower bound stated in terms of the
  ratio error over to any upper bound for that error;
- the common-state propensity identity: under a shared state law and transition kernel,
  reweighting by the propensity ratio is an exact change of measure;
- the effect of the `do` surgery on parent sets in a structural causal model.

The coverage composition takes the weighted-conformal transfer inequality as an explicit
hypothesis. That inequality is not proved here.

## Contents

| File | Provides |
| --- | --- |
| `src/FiniteExpectation.lean` | Probability mass functions on a finite index type, and their expectations. |
| `src/BinaryPinsker.lean` | Binary Kullback–Leibler divergence, its derivative and monotonicity structure, and `binary_pinsker`. |
| `src/OddsDifference.lean` | Odds, the posterior-to-ratio map, source mass, and the odds-difference identity. |
| `src/DoInterventionParents.lean` | Structural causal models, the `do` surgery, and its action on parent sets. |
| `src/Main.lean` | The results the preprint reports as machine-checked. |

## Verification map

The rows below match the results the preprint lists in its Formalization section.

| Preprint entry | Declaration in `src/Main.lean` | Checked content |
| --- | --- | --- |
| Lemma (posterior-to-ratio identity) | `PolicyShift.finite_posterior_ratio_identity` | Exact finite posterior-error to density-ratio `L¹` identity, with the `1/ρ` factor. |
| Proposition (classifier regret controls ratio error) | `PolicyShift.abs_sub_le_sqrt_klBin`, `PolicyShift.finite_mean_abs_le_sqrt_mean_kl`, `PolicyShift.domain_classifier_regret_to_ratio_l1`, `PolicyShift.balanced_domain_classifier_regret_to_ratio_l1` | Binary Pinsker, finite weighted Cauchy–Schwarz, the `1/(ργ)` bound, and its balanced specialization. |
| Result (end-to-end target coverage) | `PolicyShift.classifier_regret_coverage_composition` | Arithmetic composition conditional on the weighted-conformal transfer premise. |
| Proposition (policy-intervention ratio, common-state case) | `PolicyShift.common_state_propensity_identity` | Exact finite change of measure under a shared state law and transition kernel. |

Two supporting results, used in the file above and stated in the source, are also audited
below: `PolicyShift.odds_sub_odds` (the algebraic odds-difference identity) and the two
`doIntervene_*` lemmas (the action of the `do` surgery on parent sets in a structural
causal model).

## Audit

Every result the preprint claims as machine-checked depends only on Lean's three standard
axioms — `propext`, `Classical.choice`, and `Quot.sound`. The transcript below is the
axiom footprint of each declaration, produced by the standard Lean checker at the pinned
toolchain and Mathlib revision:

```
'PolicyShift.odds_sub_odds' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.finite_posterior_ratio_identity' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.abs_sub_le_sqrt_klBin' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.finite_mean_abs_le_sqrt_mean_kl' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.domain_classifier_regret_to_ratio_l1' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.balanced_domain_classifier_regret_to_ratio_l1' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.classifier_regret_coverage_composition' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.common_state_propensity_identity' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.doIntervene_clears_parents' depends on axioms: [propext, Classical.choice, Quot.sound]
'PolicyShift.doIntervene_preserves_other_parents' depends on axioms: [propext, Classical.choice, Quot.sound]
```

The development contains no `sorry` and declares no axioms of its own. The transcript
above was produced by the standard Lean toolchain at the pinned versions listed below;
a reader who reproduces the build can query the axiom footprint of any declaration
with the standard Lean tooling and obtain the same three-element list.

## Toolchain

- Lean `leanprover/lean4:v4.31.0` (pinned in `lean-toolchain`)
- Mathlib revision `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` (pinned in `lakefile.lean`)

No other dependency.

## Build

```sh
lake exe cache get
lake build
```

`lake build` compiles the five roots of `PolicyShift` and reports zero errors, zero
warnings, and zero remaining goals.

## License

Copyright 2026 Ayush Mittal and Dhruv Gupta. Released under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)
(`CC-BY-4.0`); see `LICENSE`. Mathlib is a separate work under the Apache License 2.0.
