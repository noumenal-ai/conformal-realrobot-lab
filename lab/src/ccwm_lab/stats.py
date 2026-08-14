from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.stats import norm, t


@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> Interval:
    if not (0 <= successes <= trials) or trials <= 0:
        raise ValueError("Invalid binomial counts")
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must lie in (0,1)")
    z = float(norm.ppf(0.5 + confidence / 2.0))
    phat = successes / trials
    denominator = 1.0 + z * z / trials
    center = (phat + z * z / (2.0 * trials)) / denominator
    half = z * np.sqrt(phat * (1.0 - phat) / trials + z * z / (4.0 * trials * trials)) / denominator
    return Interval(max(0.0, float(center - half)), min(1.0, float(center + half)))


def student_t_interval(values: Iterable[float], confidence: float = 0.95) -> Interval:
    x = np.asarray(list(values), dtype=np.float64)
    if x.ndim != 1 or x.size < 2 or not np.isfinite(x).all():
        raise ValueError("Student-t interval requires at least two finite observations")
    mean = float(x.mean())
    se = float(x.std(ddof=1) / np.sqrt(x.size))
    quantile = float(t.ppf(0.5 + confidence / 2.0, df=x.size - 1))
    return Interval(mean - quantile * se, mean + quantile * se)


def bonferroni_student_t_interval(
    values: Iterable[float],
    family_size: int,
    confidence: float = 0.95,
) -> Interval:
    if family_size <= 0:
        raise ValueError("family_size must be positive")
    alpha_family = 1.0 - confidence
    pointwise_confidence = 1.0 - alpha_family / family_size
    return student_t_interval(values, pointwise_confidence)


def mean_standard_error(values: Iterable[float]) -> tuple[float, float]:
    x = np.asarray(list(values), dtype=np.float64)
    if x.size < 2 or not np.isfinite(x).all():
        raise ValueError("Mean/SE requires at least two finite values")
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(x.size))


def cluster_bootstrap_mean(
    values: np.ndarray,
    clusters: np.ndarray,
    *,
    repetitions: int,
    seed: int,
    confidence: float,
) -> tuple[float, Interval]:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    clusters = np.asarray(clusters).reshape(-1)
    if values.shape != clusters.shape or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("Cluster bootstrap inputs must be finite and aligned")
    unique = np.unique(clusters)
    if unique.size < 2:
        raise ValueError("Cluster bootstrap requires at least two clusters")
    members = {cluster: np.flatnonzero(clusters == cluster) for cluster in unique}
    rng = np.random.default_rng(seed)
    draws = np.empty(repetitions, dtype=np.float64)
    for b in range(repetitions):
        sampled_clusters = rng.choice(unique, size=unique.size, replace=True)
        selected = np.concatenate([members[c] for c in sampled_clusters])
        draws[b] = values[selected].mean()
    alpha = 1.0 - confidence
    interval = Interval(
        float(np.quantile(draws, alpha / 2.0, method="linear")),
        float(np.quantile(draws, 1.0 - alpha / 2.0, method="linear")),
    )
    return float(values.mean()), interval
