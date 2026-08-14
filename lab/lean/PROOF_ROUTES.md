# Locked Lean proof routes

Only proof bodies between matching `BEGIN/END AUTOFORMALIZE_ONLY` markers may be edited.
Statements and imports are frozen. Use Loogle only to resolve an exact Mathlib lemma name.

## Supplied declarations: exact local routes

Statistical workspace, copied from the included measurements archive:

- `ZPM/InformationTheory/Pinsker/Binary.lean`

```lean
theorem InformationTheory.binary_pinsker
    (p q : ℝ) (hp0 : 0 ≤ p) (hp1 : p ≤ 1)
    (hq0 : 0 < q) (hq1 : q < 1) :
    2 * (p - q)^2 ≤ InformationTheory.klBin p q
```

- `ZPM/Probability/FintypePMF/Expectation.lean`

```lean
def ProbabilityTheory.FintypePMF.trueExpectation
    {α : Type*} [Fintype α] (p : FintypePMF α) (f : α → ℝ) : ℝ :=
  ∑ a : α, p.prob a * f a
```

Use `M.prob_nonneg i` and `M.prob_sum_one` from the supplied `FintypePMF` substrate.

Causal workspace, copied from the included causality archive:

- `Causality/Architecture.lean`

```lean
noncomputable def Causality.SCM.doIntervene
    (X : Finset M.V) (x : ∀ i ∈ X, M.Sp i) : SCM where
  Pa := fun i => if i ∈ X then ∅ else M.Pa i
  -- remaining fields preserve the SCM or replace the intervened mechanism
```

## Statistical workspace

Toolchain and Mathlib are fixed by `lean/statistical/`. The supplied measurements archive is
copied verbatim as `ZPM/`.

### `odds_sub_odds`

Goal:

```lean
odds u - odds v = (u - v) / ((1 - u) * (1 - v))
```

Procedure:

1. `unfold odds`.
2. Derive `1 - u ≠ 0` and `1 - v ≠ 0` from `hu`, `hv`.
3. `field_simp` using those facts.
4. `ring`.

### `finite_posterior_ratio_identity`

Unfold only `sourceMass`, `ratioFromPosterior`, and `trueExpectation`. Use `Finset.sum_congr`.
For each index:

1. Apply `odds_sub_odds` to `η i` and `h i` using `hη1 i` and `hh1 i`.
2. Rewrite absolute products/quotients with `abs_mul`, `abs_div`.
3. Derive positivity/nonzeroness of `ρ`, `1-ρ`, `1-η i`, and `1-h i` from the hypotheses.
4. Rewrite absolute values of positive factors with `abs_of_pos`.
5. `field_simp` and `ring`.

The pointwise cancellation is exactly

```text
M_i (1-eta_i)/(1-rho)
  * | ((1-rho)/rho) [eta_i/(1-eta_i)-h_i/(1-h_i)] |
= (1/rho) M_i |eta_i-h_i|/(1-h_i).
```

Do not replace the exact identity by an inequality.

### `abs_sub_le_sqrt_klBin`

1. Set
   `hb := InformationTheory.binary_pinsker p q hp0 hp1 hq0 hq1`.
2. Establish `0 ≤ klBin p q / 2` from `hb` and square nonnegativity.
3. Convert `hb` into `(p-q)^2 ≤ klBin p q / 2` with `nlinarith`.
4. Apply `Real.sqrt_le_sqrt`.
5. Rewrite `Real.sqrt ((p-q)^2)` to `|p-q|` using the Mathlib square-root square lemma
   returned by Loogle.

### `finite_mean_abs_le_sqrt_mean_kl`

Use the following fixed route; do not route through a new divergence theorem.

1. Unfold `trueExpectation` at the goal.
2. For each `i`, obtain
   `|η i-h i| ≤ sqrt (klBin (η i) (h i) / 2)` from `abs_sub_le_sqrt_klBin`.
3. Multiply by `M.prob i ≥ 0` and sum with `Finset.sum_le_sum`.
4. Apply finite weighted Cauchy-Schwarz to the nonnegative vectors
   `sqrt (M.prob i)` and
   `sqrt (M.prob i) * sqrt (klBin (η i) (h i) / 2)`.
5. Rewrite `∑ i, M.prob i = 1` using `M.prob_sum_one` and
   `Real.sq_sqrt (M.prob_nonneg i)`.
6. Use `Real.sq_sqrt` for each nonnegative `klBin/2`, whose nonnegativity follows from
   `binary_pinsker` and `sq_nonneg`.
7. Close the final square/square-root comparison with `Real.sqrt_le_sqrt`, `ring_nf`, and
   `nlinarith`.

Use the exact pinned-Mathlib theorem

```lean
Finset.sum_mul_sq_le_sq_mul_sq
  (s : Finset ι) (f g : ι → ℝ) :
  (∑ i ∈ s, f i * g i) ^ 2
    ≤ (∑ i ∈ s, f i ^ 2) * ∑ i ∈ s, g i ^ 2
```

from `Mathlib/Algebra/Order/BigOperators/Ring/Finset.lean`. No name discovery is required for
this step.

### `domain_classifier_regret_to_ratio_l1`

1. Rewrite the left side with `finite_posterior_ratio_identity`.
2. For each `i`, derive `γ ≤ 1-h i` from `hhγ i`.
3. Since `γ>0`, derive
   `|η i-h i|/(1-h i) ≤ (1/γ)|η i-h i|`.
4. Sum under `M.prob i ≥ 0`; rewrite as `trueExpectation`.
5. Invoke `finite_mean_abs_le_sqrt_mean_kl`, supplying `hη1 i |>.le` where needed.
6. Close positive-factor arithmetic with `gcongr`, `field_simp`, and `nlinarith`.

### `balanced_domain_classifier_regret_to_ratio_l1`

Invoke `domain_classifier_regret_to_ratio_l1` with `ρ=1/2`. Normalize

```text
(1 / ((1/2) * gamma)) * sqrt(E/2) = sqrt(2*E)/gamma
```

using nonnegativity of `E`, `Real.sqrt_mul`, square-root division identities returned by Loogle,
`field_simp`, `ring_nf`, and `nlinarith`. Do not restate the theorem with a weaker constant.

## Causal workspace

The supplied causality archive is copied verbatim. It is built separately because its pin differs
from the measurements archive.

### `common_state_propensity_identity`

Apply `Finset.sum_congr` at the `s`, `a`, and `y` sums. For each point:

1. From `hpos s a`, derive `πb s a ≠ 0`.
2. `field_simp` with this fact.
3. `ring`.

No probability-normalization premise is required: this is a pointwise algebraic cancellation
inside the finite sum.

### `doIntervene_clears_parents`

The `Pa` field of `SCM.doIntervene` is definitionally
`fun i => if i ∈ X then ∅ else M.Pa i`.
Use exactly:

```lean
simp [Causality.SCM.doIntervene, hi]
```

### `doIntervene_preserves_other_parents`

Use exactly:

```lean
simp [Causality.SCM.doIntervene, hi]
```

## Forbidden shortcuts

No `sorry`, `admit`, `axiom`, `unsafe`, `native_decide`, statement change, import change, helper
declaration outside a marked proof body, or alternate theorem. The post-build audit checks all of
these.
