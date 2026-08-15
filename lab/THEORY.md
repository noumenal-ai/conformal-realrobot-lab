# Domain-classifier regret implies density-ratio and coverage bounds

This file freezes the theorem used by the experiment. It is not a research prompt. The
statements, constants, and scope below must not be changed by the execution agent.

## 1. Setup

Let `P` and `Q` be probability laws on a measurable covariate space `X`, with `Q << P` and

\[
w(x)=\frac{dQ}{dP}(x).
\]

Choose a domain prior `rho in (0,1)`. Form the mixture experiment

\[
D\sim\operatorname{Bernoulli}(\rho),\qquad
X\mid D=0\sim P,\qquad X\mid D=1\sim Q,
\]

and let

\[
M=(1-\rho)P+\rho Q,
\qquad
\eta(x)=\Pr(D=1\mid X=x).
\]

For an estimated posterior `h : X -> [gamma,1-gamma]`, with `gamma in (0,1/2)`, define

\[
\widehat w_h(x)=\frac{1-\rho}{\rho}\frac{h(x)}{1-h(x)}.
\]

The population binary log-loss is

\[
R(h)=\mathbb E[-D\log h(X)-(1-D)\log(1-h(X))].
\]

Its Bayes minimizer is `eta`, and its excess risk is

\[
\Delta_{\log}(h)=R(h)-R(\eta).
\]

All logarithms are natural.

## 2. Exact posterior-to-ratio identity

By Bayes' rule in Radon-Nikodym form,

\[
\frac{dP}{dM}=\frac{1-\eta}{1-\rho},
\qquad
\frac{dQ}{dM}=\frac{\eta}{\rho}.
\]

Hence, `P`-almost everywhere,

\[
w=\frac{dQ/dM}{dP/dM}
=\frac{1-\rho}{\rho}\frac{\eta}{1-\eta}.
\]

For every `x` where the terms are defined,

\[
\left|\frac{\eta}{1-\eta}-\frac{h}{1-h}\right|
=\frac{|\eta-h|}{(1-\eta)(1-h)}.
\]

Multiplying by `dP/dM=(1-eta)/(1-rho)` gives the exact integral identity

\[
\boxed{
\mathbb E_P|w-\widehat w_h|
=
\frac1\rho\,
\mathbb E_M\!\left[\frac{|\eta-h|}{1-h}\right].
}
\tag{2.1}
\]

Because `h <= 1-gamma`,

\[
\mathbb E_P|w-\widehat w_h|
\le \frac{1}{\rho\gamma}\mathbb E_M|\eta-h|.
\tag{2.2}
\]

This is the key constant. The looser `1/gamma^2` argument obtained by globally
Lipschitz-bounding the odds map is unnecessary; cancellation against `dP/dM` improves it to
`1/(rho gamma)`.

## 3. Log-loss regret controls posterior error

Conditioning the log loss on `X=x` gives

\[
\Delta_{\log}(h)
=
\mathbb E_M\left[
\operatorname{KL}
\bigl(\operatorname{Bern}(\eta(X))\,\|\,\operatorname{Bern}(h(X))\bigr)
\right].
\tag{3.1}
\]

The supplied measurement library proves sharp binary Pinsker:

\[
2(p-q)^2\le \operatorname{klBin}(p,q).
\]

Pointwise application, followed by Cauchy-Schwarz (equivalently Jensen for the square root),
gives

\[
\begin{aligned}
\mathbb E_M|\eta-h|
&\le
\mathbb E_M\sqrt{\frac12
\operatorname{KL}(\operatorname{Bern}(\eta)\|\operatorname{Bern}(h))}\\
&\le
\sqrt{\frac12\Delta_{\log}(h)}.
\end{aligned}
\tag{3.2}
\]

Combining (2.2) and (3.2) proves the requested bound.

## 4. Main theorem

**Theorem (domain-classifier regret to density-ratio error).** Under the setup above,

\[
\boxed{
\mathbb E_P|w-\widehat w_h|
\le
\frac{1}{\rho\gamma}
\sqrt{\frac{\Delta_{\log}(h)}{2}}.
}
\tag{4.1}
\]

For the balanced domain experiment `rho=1/2`,

\[
\boxed{
\mathbb E_P|w-\widehat w_h|
\le
\frac{\sqrt{2\Delta_{\log}(h)}}{\gamma}.
}
\tag{4.2}
\]

No smoothness, parametric correctness, bounded true density ratio, or score boundedness is
used. The only overlap guardrail in this conversion is the clipping of the *estimated*
posterior away from one. When the right-hand side is greater than one, the resulting coverage
bound is valid but uninformative; the exact finite-pool TV diagnostic should then be used.

## 5. Coverage corollary

Let `(X,Y)` have source law `P_Z` and target law `Q_Z`, assume the conditional law of `Y|X`
is invariant, and let `w(X)=dQ_Z/dP_Z`. Let weighted split conformal use the estimated weight
`widehat w_h`, fitted independently of the calibration sample. The approximate-weight transfer
theorem already fixed in the paper gives

\[
\Pr_{P_Z^n\otimes Q_Z}\{Y_{n+1}\in C_{\widehat w_h}(X_{n+1})\}
\ge
1-\alpha-\mathbb E_{P_Z}|w-\widehat w_h|.
\]

Therefore

\[
\boxed{
\Pr\{Y_{n+1}\in C_{\widehat w_h}(X_{n+1})\}
\ge
1-\alpha-
\frac{1}{\rho\gamma}
\sqrt{\frac{\Delta_{\log}(h)}{2}}.
}
\tag{5.1}
\]

The sharper distribution-specific statement remains

\[
\Pr(\mathrm{cover})\ge 1-\alpha-\operatorname{TV}(Q_Z,\widehat Q_Z),
\]

where `d widehat Q_Z / dP_Z` is the normalized estimated weight. The experiment reports both
this exact finite-pool TV term and the classifier-regret upper bound.

## 6. Finite-sample interfaces

The theorem consumes any valid upper bound on `Delta_log(h)`. Two interfaces are frozen.

### 6.1 Uniform-convergence interface

If, with probability at least `1-delta`,

\[
\sup_{f\in\mathcal H}|R(f)-\widehat R_N(f)|\le u_N(\delta),
\]

if `eta` belongs to `H`, and if the returned classifier is a `zeta`-approximate empirical risk
minimizer, then

\[
\Delta_{\log}(h)\le 2u_N(\delta)+\zeta.
\]

Substitution into (4.1) is immediate. For a finite clipped class of size `K`, log loss is bounded
by `L_gamma=log(1/gamma)`, and Hoeffding plus a union bound gives the explicit choice

\[
u_N(\delta)=L_\gamma\sqrt{\frac{\log(2K/\delta)}{2N}}.
\]

This route requires realizability and is deliberately not used for the headline real-data
coverage bound.

### 6.2 Exact finite-pool interface used here

The external robot trajectories are indexed into a finite pool `Omega`. The experiment defines
`P_lambda` and `Q_lambda` exactly on that pool using an outcome-blind exponential tilt. Thus
`w`, `eta`, `M`, and the fitted classifier's population regret are all exactly computable by
finite summation:

\[
\Delta_{\log}(h)
=
\sum_{i\in\Omega} M_i
\operatorname{KL}(\operatorname{Bern}(\eta_i)\|\operatorname{Bern}(h_i)).
\]

This removes any need to estimate Bayes risk or assert classifier realizability. It is a
conditional-on-the-real-pool bound. Episode-cluster bootstrap intervals are reported
separately to describe sensitivity to the sampled physical trajectories.

## 7. Sources and inherited proof routes

- Density-ratio/class-posterior reduction: Menon and Ong, *Linking losses for density ratio and
  class-probability estimation*, ICML 2016.
- Weighted conformal under covariate shift: Tibshirani, Barber, Candes, and Ramdas,
  *Conformal Prediction Under Covariate Shift*, NeurIPS 2019.
- Binary Pinsker: supplied file
  `ZPM/InformationTheory/Pinsker/Binary.lean`, theorem
  `InformationTheory.binary_pinsker`.
- Finite expectations and event transfer: supplied files under
  `ZPM/Probability/FintypePMF/`.
- General total variation and Pinsker: supplied files
  `ZPM/MeasureTheory/ProbabilityMeasure/TotalVariation/Real.lean` and
  `ZPM/InformationTheory/Pinsker/General.lean`.

The Lean task is proof engineering only: formalize (2.1), invoke the supplied binary Pinsker
lemma pointwise, prove the finite weighted Cauchy-Schwarz step, and compose. No theorem
statement may be weakened or changed.
