# Lean build scope

The two builds verify exactly the following locked objects.

## Statistical workspace

Using the included measurements archive and its pinned Mathlib version:

1. the algebraic odds-difference identity;
2. the exact finite-pool posterior-to-density-ratio L1 identity;
3. binary Pinsker converted to an absolute Bernoulli-posterior error bound;
4. the finite weighted Cauchy-Schwarz step;
5. the theorem
   `ratio L1 error <= (1/(rho*gamma))*sqrt(mean binary KL/2)`;
6. the balanced-domain specialization with constant `sqrt(2*mean KL)/gamma`;
7. the arithmetic composition with an approximate-weight coverage-transfer premise.

Item 7 does not re-formalize weighted conformal prediction. It locks the exact composition step
used after the paper's separately stated approximate-weight conformal theorem. No stronger Lean
claim is made.

## Causal workspace

Using the included causality archive and its separate pinned Mathlib version:

1. the exact finite common-state propensity reweighting identity;
2. the definitional fact that `SCM.doIntervene` clears incoming parents at intervened vertices;
3. the definitional fact that it preserves parent sets elsewhere.

## Build isolation

The supplied archives have incompatible toolchain/Mathlib pins. They are never merged. Each Lake
workspace copies only its corresponding supplied source tree and builds separately.

## Execution-agent boundary

The statements and imports are hash-locked. Codex may fill only marked proof bodies. A successful
run compiles both workspaces, runs `#print axioms` audits, rejects unresolved placeholders and
forbidden proof shortcuts, and rechecks the statement contract after compilation.
