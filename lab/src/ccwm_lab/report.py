from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .io_utils import atomic_write_json
from .stats import (
    bonferroni_student_t_interval,
    cluster_bootstrap_mean,
    mean_standard_error,
    student_t_interval,
)


def _finite_mean(series: pd.Series) -> float:
    values = series.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    return float(finite.mean()) if finite.size else float("inf")


def summarize_results(results: pd.DataFrame, confidence: float) -> pd.DataFrame:
    keys = ["lambda", "alpha", "method"]
    groups = list(results.groupby(keys, sort=True))
    family_size = len(groups)
    rows: list[dict[str, Any]] = []
    for (lam, alpha, method), group in groups:
        coverage = group["coverage"].to_numpy(dtype=float)
        point = student_t_interval(coverage, confidence)
        simultaneous = bonferroni_student_t_interval(coverage, family_size, confidence)
        mean, se = mean_standard_error(coverage)
        rows.append(
            {
                "lambda": float(lam),
                "alpha": float(alpha),
                "method": str(method),
                "repetitions": int(len(group)),
                "coverage_mean": mean,
                "coverage_se": se,
                "coverage_ci_lower": point.lower,
                "coverage_ci_upper": point.upper,
                "coverage_simultaneous_lower": simultaneous.lower,
                "coverage_simultaneous_upper": simultaneous.upper,
                "finite_radius_mean": _finite_mean(group["finite_radius_mean"]),
                "finite_radius_median_mean": _finite_mean(group["finite_radius_median"]),
                "infinite_radius_rate_mean": float(group["infinite_radius_rate"].mean()),
                "ess_mean": float(group["effective_sample_size"].mean()),
                "exact_tv_mean": float(group["exact_tv"].mean()),
                "exact_l1_mean": float(group["exact_l1_ratio_error"].mean()),
                "population_logistic_regret_mean": float(group["population_logistic_regret"].mean()),
                "classifier_l1_bound_mean": float(group["classifier_regret_l1_bound"].mean()),
                "exact_tv_lower_bound_mean": float(group["exact_tv_lower_bound"].mean()),
                "classifier_lower_bound_mean": float(group["classifier_regret_lower_bound"].mean()),
                "coverage_minus_tv_bound_mean": float(
                    (group["coverage"] - group["exact_tv_lower_bound"]).mean()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(keys).reset_index(drop=True)


def validate_results(results: pd.DataFrame, protocol: dict[str, Any]) -> tuple[bool, list[str]]:
    messages: list[str] = []
    hard = protocol["hard_gates"]
    conf = protocol["conformal"]
    expected = (
        len(protocol["shift_design"]["lambdas"])
        * int(conf["repetitions"])
        * len(conf["alphas"])
        * len(conf["methods"])
    )
    if len(results) != expected:
        messages.append(f"FAIL: expected {expected} preregistered rows, observed {len(results)}")

    required_numeric = [
        "coverage",
        "exact_tv",
        "exact_l1_ratio_error",
        "population_logistic_regret",
        "classifier_regret_l1_bound",
        "effective_sample_size",
    ]
    for column in required_numeric:
        values = results[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            messages.append(f"FAIL: non-finite values in required column {column}")

    tol_num = 1e-8
    if (results["exact_tv"] > np.minimum(1.0, results["exact_l1_ratio_error"]) + tol_num).any():
        messages.append("FAIL: exact TV exceeds the normalized L1 transfer bound")
    if (results["exact_l1_ratio_error"] > results["classifier_regret_l1_bound"] + tol_num).any():
        bad = results.loc[
            results["exact_l1_ratio_error"] > results["classifier_regret_l1_bound"] + tol_num,
            ["lambda", "repetition", "method", "exact_l1_ratio_error", "classifier_regret_l1_bound"],
        ].head()
        messages.append("FAIL: classifier-regret theorem inequality violated\n" + bad.to_string(index=False))

    oracle_tolerance = float(hard["reject_oracle_gross_undercoverage_tolerance"])
    theorem_tolerance = float(hard["reject_theorem_violation_tolerance"])
    for (lam, alpha, method), group in results.groupby(["lambda", "alpha", "method"]):
        if method == "oracle_ratio":
            mean, se = mean_standard_error(group["coverage"])
            nominal = 1.0 - float(alpha)
            if mean + 3.0 * se < nominal - oracle_tolerance:
                messages.append(
                    f"FAIL: oracle gross undercoverage at lambda={lam}, alpha={alpha}: "
                    f"mean={mean:.6f}, 3SE={3*se:.6f}, nominal={nominal:.6f}"
                )
        gap = group["coverage"] - group["exact_tv_lower_bound"]
        mean_gap, se_gap = mean_standard_error(gap)
        if mean_gap + 3.0 * se_gap < -theorem_tolerance:
            messages.append(
                f"FAIL: empirical mean is grossly below exact TV theorem bound at "
                f"lambda={lam}, alpha={alpha}, method={method}: gap={mean_gap:.6f}, 3SE={3*se_gap:.6f}"
            )

    if not messages:
        messages.append("PASS: every preregistered cell is present and every mechanical theorem/coverage gate passed")
        return True, messages
    return False, messages


def write_pool_bootstrap(pool: pd.DataFrame, protocol: dict[str, Any], output_dir: Path) -> pd.DataFrame:
    cfg = protocol["statistics"]
    metrics = ["score", "translation_action_norm", "rotation_action_norm", "gripper_action_abs"]
    rows: list[dict[str, Any]] = []
    clusters = pool["episode_id"].to_numpy()
    for offset, metric in enumerate(metrics):
        mean, interval = cluster_bootstrap_mean(
            pool[metric].to_numpy(dtype=float),
            clusters,
            repetitions=int(cfg["cluster_bootstrap_repetitions"]),
            seed=int(cfg["cluster_bootstrap_seed"]) + offset,
            confidence=float(cfg["confidence_level"]),
        )
        rows.append({"metric": metric, "mean": mean, "cluster_ci_lower": interval.lower, "cluster_ci_upper": interval.upper})
    frame = pd.DataFrame(rows)
    frame.to_csv(output_dir / "pool_episode_cluster_bootstrap.csv", index=False)
    return frame


def _method_label(method: str) -> str:
    return {
        "unweighted": "Unweighted",
        "oracle_ratio": "Oracle ratio",
        "estimated_ratio": "Estimated ratio",
        "estimated_ratio_clipped": "Estimated + clip(5)",
    }[method]


def write_latex_table(summary: pd.DataFrame, output_path: Path, alpha: float = 0.10) -> None:
    view = summary[np.isclose(summary["alpha"], alpha)].copy()
    lines = [
        "\\begin{tabular}{clrrrr}",
        "\\toprule",
        "$\\lambda$ & Method & Coverage & Radius & ESS & $\\mathrm{TV}(Q,\\widehat Q)$ \\\\",
        "\\midrule",
    ]
    for lam in sorted(view["lambda"].unique()):
        block = view[np.isclose(view["lambda"], lam)]
        for _, row in block.iterrows():
            cov = f"{row.coverage_mean:.3f} [{row.coverage_ci_lower:.3f},{row.coverage_ci_upper:.3f}]"
            radius = "inf" if not np.isfinite(row.finite_radius_median_mean) else f"{row.finite_radius_median_mean:.3f}"
            lines.append(
                f"{lam:.1f} & {_method_label(row.method)} & {cov} & {radius} & "
                f"{row.ess_mean:.1f} & {row.exact_tv_mean:.3f} \\\\" 
            )
        lines.append("\\midrule")
    lines[-1] = "\\bottomrule"
    lines.append("\\end{tabular}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figures(summary: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    view = summary[np.isclose(summary["alpha"], 0.10)]

    fig, ax = plt.subplots()
    for method, block in view.groupby("method"):
        block = block.sort_values("lambda")
        ax.errorbar(
            block["lambda"],
            block["coverage_mean"],
            yerr=[
                block["coverage_mean"] - block["coverage_ci_lower"],
                block["coverage_ci_upper"] - block["coverage_mean"],
            ],
            marker="o",
            capsize=3,
            label=_method_label(method),
        )
    ax.axhline(0.90, linestyle="--", linewidth=1)
    ax.set_xlabel("Shift strength $\\lambda$")
    ax.set_ylabel("Target coverage ($\\alpha=0.1$)")
    ax.set_ylim(0.0, 1.02)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "coverage_vs_shift.pdf")
    fig.savefig(output_dir / "coverage_vs_shift.png", dpi=200)
    plt.close(fig)

    est = view[view["method"] == "estimated_ratio"].sort_values("lambda")
    fig, ax = plt.subplots()
    ax.plot(est["lambda"], est["coverage_mean"], marker="o", label="Empirical coverage")
    ax.plot(est["lambda"], est["exact_tv_lower_bound_mean"], marker="o", label="Exact TV lower bound")
    ax.plot(est["lambda"], est["classifier_lower_bound_mean"], marker="o", label="Classifier-regret lower bound")
    ax.set_xlabel("Shift strength $\\lambda$")
    ax.set_ylabel("Coverage / certified lower bound")
    ax.set_ylim(0.0, 1.02)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "certificate_diagnostics.pdf")
    fig.savefig(output_dir / "certificate_diagnostics.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots()
    for method, block in view.groupby("method"):
        block = block.sort_values("lambda")
        ax.plot(block["lambda"], block["ess_mean"], marker="o", label=_method_label(method))
    ax.set_xlabel("Shift strength $\\lambda$")
    ax.set_ylabel("Calibration effective sample size")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "ess_vs_shift.pdf")
    fig.savefig(output_dir / "ess_vs_shift.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots()
    for method, block in view.groupby("method"):
        block = block.sort_values("lambda").copy()
        block["finite_radius_median_mean"] = block["finite_radius_median_mean"].replace(
            [np.inf, -np.inf], np.nan
        )
        ax.plot(block["lambda"], block["finite_radius_median_mean"], marker="o", label=_method_label(method))
    ax.set_xlabel("Shift strength $\\lambda$")
    ax.set_ylabel("Mean repetition-level median latent radius")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "radius_vs_shift.pdf")
    fig.savefig(output_dir / "radius_vs_shift.png", dpi=200)
    plt.close(fig)


def analyze_and_report(
    *,
    results_csv: Path,
    pool_csv: Path,
    protocol: dict[str, Any],
    output_dir: Path,
) -> tuple[pd.DataFrame, bool]:
    results = pd.read_csv(results_csv)
    pool = pd.read_csv(pool_csv)
    confidence = float(protocol["statistics"]["confidence_level"])
    summary = summarize_results(results, confidence)
    summary.to_csv(output_dir / "summary.csv", index=False)
    write_pool_bootstrap(pool, protocol, output_dir)
    write_latex_table(summary, output_dir / "main_results_table.tex")
    write_figures(summary, output_dir / "figures")
    passed, messages = validate_results(results, protocol)
    report = ["# Validation report", "", f"FINAL STATUS: {'PASS' if passed else 'FAIL'}", ""]
    report.extend(f"- {message}" for message in messages)
    report.extend(
        [
            "",
            "## Scope",
            "",
            "The result is conditional on the indexed finite pool of external physical-robot transitions. ",
            "All outcome data and model scores are real/upstream; only index sampling is randomized.",
        ]
    )
    (output_dir / "VALIDATION_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    safe_summary = summary.astype(object).where(pd.notna(summary), None)
    for column in safe_summary.columns:
        safe_summary[column] = safe_summary[column].map(
            lambda value: None if isinstance(value, (float, np.floating)) and not np.isfinite(value) else value
        )
    atomic_write_json(
        output_dir / "summary.json",
        {
            "status": "PASS" if passed else "FAIL",
            "rows": safe_summary.to_dict(orient="records"),
        },
    )
    return summary, passed
