# Frozen statistical toolkit

This is the complete computation specification for the final outputs. The execution agent may
implement none of these differently.

## Finite-pool laws

For indexed real transitions `i=1,...,N`, compute the outcome-blind statistic `g_i` as the
empirical midrank of translational action norm mapped to `[-1,1]`. For each fixed `lambda`,

\[
P_i=\frac{e^{-\lambda g_i}}{\sum_j e^{-\lambda g_j}},\qquad
Q_i=\frac{e^{+\lambda g_i}}{\sum_j e^{+\lambda g_j}},\qquad
w_i=Q_i/P_i.
\]

For domain prior `rho`,

\[
M_i=(1-\rho)P_i+\rho Q_i,\qquad
\eta_i=\frac{\rho w_i}{1-\rho+\rho w_i}.
\]

## Domain classifier and certificate

Fit the preregistered one-feature ridge logistic classifier on independent source and target
index draws. Clip its posterior to `[gamma,1-gamma]` and set

\[
\widehat w_i=\frac{1-\rho}{\rho}\frac{h_i}{1-h_i}.
\]

Compute by exact finite summation

\[
\Delta_{\log}=\sum_i M_i\,\mathrm{KL}(\mathrm{Bern}(\eta_i)\|\mathrm{Bern}(h_i)),
\]

\[
\varepsilon_1=\sum_i P_i|w_i-\widehat w_i|,
\qquad
B_{\rm clf}=\frac{1}{\rho\gamma}\sqrt{\Delta_{\log}/2}.
\]

The mechanical theorem gate is `epsilon_1 <= B_clf` up to `1e-8` numerical tolerance.

For any nonnegative method weight `v`, normalize

\[
\widehat Q_i=\frac{P_i v_i}{\sum_jP_jv_j},
\qquad
\mathrm{TV}(Q,\widehat Q)=\frac12\sum_i|Q_i-\widehat Q_i|.
\]

The second theorem gate is

\[
\mathrm{TV}(Q,\widehat Q)\le \min\{1,\sum_iP_i|w_i-v_i|\}.
\]

## Weighted split-conformal radius

For calibration scores `R_i`, calibration weights `v_i`, and a test weight `v_*`, form the
probability measure

\[
\sum_{i=1}^n\frac{v_i}{\sum_jv_j+v_*}\delta_{R_i}
+\frac{v_*}{\sum_jv_j+v_*}\delta_{+\infty}.
\]

The radius is its lower `(1-alpha)` quantile. Coverage is `1{R_* <= radius}`. Report the rate of
infinite radii explicitly.

## Efficiency and transfer diagnostics

\[
\mathrm{ESS}(v_{1:n})=\frac{(\sum_i v_i)^2}{\sum_i v_i^2}.
\]

Report the three lower bounds without truncating them in raw outputs:

\[
1-\alpha-\mathrm{TV}(Q,\widehat Q),\qquad
1-\alpha-\varepsilon_1,\qquad
1-\alpha-B_{\rm clf}.
\]

## Repetition-level uncertainty

The independent analysis unit is one complete fixed-seed repetition. For each preregistered
`(lambda,alpha,method)` cell, report the mean, standard error, and two-sided Student-t interval
across 50 repetitions. For a family of `K` cells, the simultaneous interval uses pointwise
confidence `1-(1-confidence)/K` (Bonferroni).

For each repetition's target-test count `(successes,trials)`, save the two-sided Wilson interval.

## Physical-trajectory sensitivity

Resample episode IDs with replacement, retain all indexed transitions in every selected episode,
and recompute each pool mean. Use the percentile interval from 2,000 fixed-seed cluster-bootstrap
draws. This describes finite-pool sensitivity; it is not substituted for the conditional theorem.

## Output discipline

All raw repetitions, classifier fits, exact finite-pool laws, pool bootstrap results, summaries,
figures, LaTeX fragments, environment metadata, source revisions, and SHA-256 hashes must be
written. No failed cell may be dropped and no interval may be selected after looking at results.
