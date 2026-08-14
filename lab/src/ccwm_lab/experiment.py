from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .conformal import evaluate_weighted_conformal
from .ratio import (
    classifier_regret_l1_bound,
    empirical_midrank_unit,
    exponential_tilt_laws,
    fit_ridge_logistic,
    l1_ratio_error,
    mixture_mass,
    normalized_surrogate,
    population_logistic_regret,
    posterior_from_ratio,
    posterior_ratio_identity_lhs_rhs,
    predict_posterior,
    ratio_from_posterior,
    total_variation,
)
from .stats import wilson_interval


def _method_diagnostics(
    *,
    p: np.ndarray,
    q: np.ndarray,
    w: np.ndarray,
    eta: np.ndarray,
    m: np.ndarray,
    v: np.ndarray,
    h: np.ndarray,
    rho: float,
    gamma: float,
    method: str,
) -> dict[str, float]:
    qhat = normalized_surrogate(p, v)
    tv = total_variation(q, qhat)
    l1 = l1_ratio_error(p, w, v)
    regret = 0.0 if method == "oracle_ratio" else population_logistic_regret(m, eta, h)
    classifier_bound = 0.0 if method == "oracle_ratio" else classifier_regret_l1_bound(regret, rho, gamma)
    return {
        "exact_tv": tv,
        "exact_l1_ratio_error": l1,
        "population_logistic_regret": regret,
        "classifier_regret_l1_bound": classifier_bound,
        "surrogate_normalizer": float(np.sum(p * v)),
        "pool_weight_min": float(np.min(v)),
        "pool_weight_max": float(np.max(v)),
    }


def run_experiment_battery(
    *,
    scored_pool_csv: Path,
    protocol: dict[str, Any],
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pool = pd.read_csv(scored_pool_csv)
    required = {
        "sample_id",
        "episode_id",
        "task",
        "score",
        "translation_action_norm",
    }
    missing = required.difference(pool.columns)
    if missing:
        raise ValueError(f"Scored pool is missing columns: {sorted(missing)}")
    if pool["sample_id"].duplicated().any():
        raise ValueError("Duplicate sample IDs in scored pool")
    if not np.isfinite(pool["score"].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite model score in pool")

    g = empirical_midrank_unit(pool["translation_action_norm"].to_numpy(dtype=float))
    pool = pool.copy()
    pool["shift_statistic_g"] = g
    output_dir.mkdir(parents=True, exist_ok=True)
    pool.to_csv(output_dir / "pool_with_shift.csv", index=False)

    shift_cfg = protocol["shift_design"]
    ratio_cfg = protocol["ratio_estimation"]
    conf_cfg = protocol["conformal"]
    stats_cfg = protocol["statistics"]

    lambdas = [float(v) for v in shift_cfg["lambdas"]]
    alphas = [float(v) for v in conf_cfg["alphas"]]
    repetitions = int(conf_cfg["repetitions"])
    seed_base = int(conf_cfg["seed_base"])
    n_cal = int(conf_cfg["calibration_size"])
    n_test = int(conf_cfg["target_test_size"])
    rho = float(ratio_cfg["domain_prior_rho"])
    gamma = float(ratio_cfg["posterior_clip_gamma"])
    n_src = int(ratio_cfg["source_domain_samples"])
    n_tgt = int(ratio_cfg["target_domain_samples"])
    ratio_cap = float(conf_cfg["estimated_ratio_cap"])
    confidence = float(stats_cfg["confidence_level"])
    if not np.isclose(rho, 0.5) or n_src != n_tgt:
        raise ValueError("The frozen experiment requires a balanced domain prior and equal domain sample counts")
    if not np.isclose(ratio_cap, 5.0):
        raise ValueError("The frozen clipping ablation is fixed at ratio cap 5")

    scores = pool["score"].to_numpy(dtype=np.float64)
    n_pool = len(pool)
    results: list[dict[str, Any]] = []
    classifier_rows: list[dict[str, Any]] = []
    law_rows: list[dict[str, Any]] = []

    for lambda_index, lam in enumerate(lambdas):
        p, q, w = exponential_tilt_laws(g, lam)
        m = mixture_mass(p, q, rho)
        eta = posterior_from_ratio(w, rho)
        expected_slope = 2.0 * lam
        # For the balanced domain experiment, logit(eta)=log(q/p)=intercept+2 lambda g.
        expected_intercept = float(np.mean(np.log(w) - expected_slope * g))
        bayes_logits = np.log(eta) - np.log1p(-eta)
        linear_logits = expected_intercept + expected_slope * g
        if not np.allclose(bayes_logits, linear_logits, rtol=1e-10, atol=1e-10):
            raise AssertionError("Frozen tilt no longer has the preregistered linear Bayes domain logit")
        law_rows.append(
            {
                "lambda": lam,
                "pool_size": n_pool,
                "source_entropy": float(-np.sum(p * np.log(p))),
                "target_entropy": float(-np.sum(q * np.log(q))),
                "oracle_ratio_min": float(w.min()),
                "oracle_ratio_max": float(w.max()),
                "oracle_ratio_mean_under_source": float(np.sum(p * w)),
                "bayes_logit_slope": expected_slope,
                "bayes_logit_intercept": expected_intercept,
                "source_target_tv": total_variation(p, q),
            }
        )

        for repetition in range(repetitions):
            seed_sequence = np.random.SeedSequence(seed_base + 100_000 * lambda_index + repetition)
            ratio_seed, calibration_seed, test_seed = seed_sequence.spawn(3)
            ratio_rng = np.random.default_rng(ratio_seed)
            calibration_rng = np.random.default_rng(calibration_seed)
            test_rng = np.random.default_rng(test_seed)

            source_domain_idx = ratio_rng.choice(n_pool, size=n_src, replace=True, p=p)
            target_domain_idx = ratio_rng.choice(n_pool, size=n_tgt, replace=True, p=q)
            domain_g = np.concatenate([g[source_domain_idx], g[target_domain_idx]])
            domain_y = np.concatenate([np.zeros(n_src), np.ones(n_tgt)])
            fit = fit_ridge_logistic(
                domain_g,
                domain_y,
                ridge=float(ratio_cfg["ridge"]),
                max_iterations=int(ratio_cfg["max_iterations"]),
                tolerance=float(ratio_cfg["tolerance"]),
            )
            h_est = predict_posterior(fit, g, gamma)
            what = ratio_from_posterior(h_est, rho)
            what_clipped = np.minimum(what, ratio_cap)
            h_clipped = posterior_from_ratio(what_clipped, rho)
            h_unweighted = np.full(n_pool, rho, dtype=np.float64)
            for label, posterior in {"estimated": h_est, "ratio_clipped": h_clipped, "unweighted": h_unweighted}.items():
                if (posterior < gamma - 1e-12).any() or (posterior > 1.0 - gamma + 1e-12).any():
                    raise AssertionError(f"{label} posterior violates the frozen clipping interval")

            lhs, rhs = posterior_ratio_identity_lhs_rhs(p, q, eta, h_est, rho)
            if not np.isclose(lhs, rhs, rtol=1e-9, atol=1e-11):
                raise AssertionError(f"Posterior-ratio identity failed numerically: {lhs} vs {rhs}")

            methods: dict[str, tuple[np.ndarray, np.ndarray]] = {
                "unweighted": (np.ones(n_pool, dtype=np.float64), h_unweighted),
                "oracle_ratio": (w, eta),
                "estimated_ratio": (what, h_est),
                "estimated_ratio_clipped": (what_clipped, h_clipped),
            }
            if list(methods) != list(conf_cfg["methods"]):
                raise AssertionError("Method order/configuration was changed")

            diagnostics = {
                name: _method_diagnostics(
                    p=p,
                    q=q,
                    w=w,
                    eta=eta,
                    m=m,
                    v=weights,
                    h=posterior,
                    rho=rho,
                    gamma=gamma,
                    method=name,
                )
                for name, (weights, posterior) in methods.items()
            }

            calibration_idx = calibration_rng.choice(n_pool, size=n_cal, replace=True, p=p)
            target_idx = test_rng.choice(n_pool, size=n_test, replace=True, p=q)
            calibration_scores = scores[calibration_idx]
            target_scores = scores[target_idx]

            classifier_rows.append(
                {
                    "lambda": lam,
                    "repetition": repetition,
                    "seed": seed_base + 100_000 * lambda_index + repetition,
                    "intercept": fit.intercept,
                    "slope": fit.coefficients[0],
                    "expected_intercept": expected_intercept,
                    "expected_slope": expected_slope,
                    "optimizer_iterations": fit.iterations,
                    "optimizer_objective": fit.objective,
                    "optimizer_status": fit.status,
                    "posterior_ratio_identity_lhs": lhs,
                    "posterior_ratio_identity_rhs": rhs,
                }
            )

            for method, (pool_weights, _) in methods.items():
                cal_weights = pool_weights[calibration_idx]
                test_weights = pool_weights[target_idx]
                diag = diagnostics[method]
                for alpha in alphas:
                    evaluation = evaluate_weighted_conformal(
                        calibration_scores=calibration_scores,
                        test_scores=target_scores,
                        calibration_weights=cal_weights,
                        test_weights=test_weights,
                        alpha=alpha,
                    )
                    wilson = wilson_interval(evaluation.successes, evaluation.trials, confidence)
                    row: dict[str, Any] = {
                        "lambda": lam,
                        "repetition": repetition,
                        "alpha": alpha,
                        "method": method,
                        "seed": seed_base + 100_000 * lambda_index + repetition,
                        **evaluation.to_dict(),
                        **diag,
                        "wilson_lower": wilson.lower,
                        "wilson_upper": wilson.upper,
                        "nominal_coverage": 1.0 - alpha,
                        "exact_tv_lower_bound": 1.0 - alpha - diag["exact_tv"],
                        "l1_lower_bound": 1.0 - alpha - diag["exact_l1_ratio_error"],
                        "classifier_regret_lower_bound": 1.0
                        - alpha
                        - diag["classifier_regret_l1_bound"],
                        "calibration_unique_fraction": float(np.unique(calibration_idx).size / n_cal),
                        "test_unique_fraction": float(np.unique(target_idx).size / n_test),
                    }
                    results.append(row)

    results_df = pd.DataFrame(results)
    classifier_df = pd.DataFrame(classifier_rows)
    laws_df = pd.DataFrame(law_rows)
    expected_cells = len(lambdas) * repetitions * len(alphas) * len(conf_cfg["methods"])
    if len(results_df) != expected_cells:
        raise AssertionError(f"Missing preregistered cells: expected {expected_cells}, got {len(results_df)}")
    results_df.to_csv(output_dir / "replicate_results.csv", index=False)
    classifier_df.to_csv(output_dir / "classifier_fits.csv", index=False)
    laws_df.to_csv(output_dir / "shift_laws.csv", index=False)
    return results_df, classifier_df, laws_df
