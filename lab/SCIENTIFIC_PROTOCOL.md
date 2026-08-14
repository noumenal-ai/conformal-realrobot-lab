# Frozen scientific protocol

## Question

Can a fixed, externally released real-robot world model be wrapped by weighted conformal
prediction so that one-step latent prediction sets retain target-law marginal coverage under a
known and estimated state-action covariate shift?

## What is real and what is randomized

Every image, robot state, and next observation comes from the official external
`franka_custom` physical-robot dataset released with `facebookresearch/jepa-wms`. The action
covariate is deterministically derived from observed endpoint robot poses by the upstream
`poses_to_diffs` routine, exactly as in the released DINO-WM data loader. The predictor is the
official pretrained `dino_wm_droid` checkpoint. The package contains no simulated transition,
generated image, synthetic noise model, simulator, or toy predictor.

Randomness is used only to sample indices from explicitly defined probability laws over the
fixed real transition pool, to split independent ratio/calibration/test draws, and to form
bootstrap intervals. This is experimental randomization, not synthetic outcome generation.

## Prediction object

For each indexed transition:

1. Two real frames at 4 Hz are the context.
2. Two real actions are computed exactly by the upstream `poses_to_diffs` routine from consecutive
   pose differences: earlier context to current context, and current context to target. They are
   aligned one-to-one with the two visual context timesteps, as required by the locked model's
   teacher-forced prediction interface.
3. The frozen DINO-WM predicts the next visual latent.
4. The target is the frozen encoder representation of the actual next real frame.
5. The nonconformity score is latent root-mean-squared error.
6. A conformal prediction set is the latent ball centered at the world-model prediction with
   the returned weighted radius.

No model is trained or fine-tuned.

## Controlled real-data shift

Let `Omega` be the finite indexed pool. Let `g_i in [-1,1]` be the empirical midrank transform
of the translational norm of the current-context-to-target action covariate. It never inspects the
target RGB frame, frozen-model target latent, or model residual. Because the released action
representation is reconstructed from endpoint poses, this battery is explicitly a statistical
covariate-shift experiment, not a prospective action-intervention experiment. For each preregistered `lambda`, define

```
P_lambda(i) proportional to exp(-lambda * g_i)
Q_lambda(i) proportional to exp(+lambda * g_i)
```

on the same support. This guarantees:

- exact absolute continuity;
- a bounded known oracle ratio;
- exact preservation of the empirical conditional law of the target given `X`;
- a nontrivial, interpretable policy-like shift toward larger actions;
- exact computation of oracle ratio, surrogate TV, L1 error, and population classifier regret.

This is a covariate-shift experiment on physical trajectories. It is not represented as a
natural deployed policy intervention. The common-state propensity theorem remains a distinct
causal specialization in the paper.

## Estimator

A balanced source-vs-target domain sample is drawn independently of conformal calibration.
The only classifier feature is the preregistered shift statistic `g`. A deterministic ridge
logistic regression is fitted with fixed optimizer settings. Its posterior is clipped to
`[0.05,0.95]`, then converted to a density ratio by posterior odds. No cross-validation,
hyperparameter search, architecture search, early-stopping choice, or post-result adjustment is
permitted.

## Methods

All methods use the identical frozen predictor and identical calibration scores:

- unweighted;
- exact oracle ratio;
- estimated ratio;
- estimated ratio clipped at 5.

The last method is an efficiency/robustness ablation. Its exact induced-surrogate TV is reported.

## Grid and repetitions

- Shift strengths: `lambda = 0, 0.5, 1.0, 1.5`.
- Miscoverage levels: `alpha = 0.05, 0.10, 0.20`.
- Calibration size: 500, sampled with replacement from `P_lambda`.
- Target test size: 10,000 per repetition, sampled with replacement from `Q_lambda`.
- Independent repetitions: 50, with seeds fixed in `config/protocol.yaml`.

No cell may be removed after execution.

## Primary outputs

For every model/shift/alpha/method cell:

- target coverage;
- mean and median finite radius;
- infinite-radius frequency;
- calibration effective sample size;
- exact finite-pool `TV(Q,Qhat)`;
- exact `E_P |w-what|`;
- exact population domain-logistic regret;
- classifier-regret ratio bound;
- theorem lower bound `1-alpha-TV`;
- theorem lower bound from classifier regret;
- repeated-run pointwise and simultaneous confidence intervals.

## Statistical treatment

The repetition is the primary independent unit. Headline intervals are Student-t intervals over
50 repetition-level estimates. Bonferroni-adjusted simultaneous intervals across the complete
preregistered grid are also emitted. Wilson intervals are saved for each repetition's finite
target test sample. Episode-cluster bootstrap summaries quantify sensitivity to which physical
trajectories appear in the finite pool; they are not substituted for the conditional finite-pool
theorem.

## Feasibility amendment (2026-08-15)

Authenticated acquisition of the locked external dataset produced 192 eligible transitions under
the unchanged episode allowlist and temporal indexing rules. The original 256-transition minimum
therefore stopped execution before model scoring or examination of any experimental outcome. The
investigator subsequently authorized a minimum pool size of 192. This amendment changes only that
feasibility threshold and the experiment identifier; all sampling laws, sample sizes, seeds,
methods, estimands, and hard validation gates remain unchanged. Domain, calibration, and target
draws continue to be sampled with replacement from the fixed finite pool.

## Frozen-model interface amendment (2026-08-15)

The first pool-192 execution exposed a tensor mismatch before any model score was emitted: the
two-frame visual context was passed to the released predictor with only the current-to-target
action. The locked training implementation pairs every visual timestep with its corresponding
action and predicts the following timestep. The amended adapter therefore reconstructs both
consecutive observed pose differences, passes the resulting two-step action sequence beside the
two visual context frames, and scores only the final prediction against the observed target. A
one-transition smoke test confirmed exact time-axis and latent-shape agreement. This amendment
does not alter the checkpoint, encoder, images, target, score function, shift statistic, sampling
law, seeds, methods, or analysis gates.

## Mechanical failure gates

Execution stops rather than improvises when any of the following occurs:

- an external repository is not at its locked commit;
- a model/data asset is not from the allowlisted official repository;
- fewer than eight episodes or 192 transitions survive indexing;
- a shift statistic depends on the target frame or residual;
- ratio fitting reuses calibration draws;
- any preregistered result cell is missing;
- oracle coverage is grossly incompatible with nominal coverage beyond the fixed tolerance;
- empirical coverage grossly violates the exact TV transfer lower bound beyond the fixed
  Monte Carlo tolerance;
- Lean contains `sorry`, `admit`, or a new `axiom` after autoformalization;
- the execution agent changes a sealed scientific or experiment file.
