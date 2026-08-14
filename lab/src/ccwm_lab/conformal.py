from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ConformalEvaluation:
    successes: int
    trials: int
    coverage: float
    finite_radius_mean: float
    finite_radius_median: float
    infinite_radius_rate: float
    effective_sample_size: float
    max_calibration_weight: float
    weight_coefficient_of_variation: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def effective_sample_size(weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=np.float64)
    numerator = float(weights.sum()) ** 2
    denominator = float(np.dot(weights, weights))
    if denominator <= 0:
        raise ValueError("Effective sample size is undefined for all-zero weights")
    return numerator / denominator


def weighted_conformal_radii(
    calibration_scores: np.ndarray,
    calibration_weights: np.ndarray,
    test_weights: np.ndarray,
    alpha: float,
) -> np.ndarray:
    scores = np.asarray(calibration_scores, dtype=np.float64).reshape(-1)
    cal_w = np.asarray(calibration_weights, dtype=np.float64).reshape(-1)
    test_w = np.asarray(test_weights, dtype=np.float64).reshape(-1)
    if scores.shape != cal_w.shape or scores.size == 0:
        raise ValueError("Calibration scores and weights must be nonempty and aligned")
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must lie in (0,1)")
    if not np.isfinite(scores).all() or (scores < 0).any():
        raise ValueError("Calibration scores must be finite and nonnegative")
    if not np.isfinite(cal_w).all() or not np.isfinite(test_w).all():
        raise ValueError("Conformal weights must be finite")
    if (cal_w < 0).any() or (test_w < 0).any():
        raise ValueError("Conformal weights must be nonnegative")
    total_cal = float(cal_w.sum())
    if total_cal <= 0:
        raise ValueError("Calibration weight sum must be positive")

    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    cumulative = np.cumsum(cal_w[order])
    thresholds = (1.0 - alpha) * (total_cal + test_w)
    indices = np.searchsorted(cumulative, thresholds, side="left")
    radii = np.full(test_w.shape, np.inf, dtype=np.float64)
    finite = indices < scores.size
    radii[finite] = sorted_scores[indices[finite]]
    return radii


def evaluate_weighted_conformal(
    *,
    calibration_scores: np.ndarray,
    test_scores: np.ndarray,
    calibration_weights: np.ndarray,
    test_weights: np.ndarray,
    alpha: float,
) -> ConformalEvaluation:
    test_scores = np.asarray(test_scores, dtype=np.float64).reshape(-1)
    radii = weighted_conformal_radii(
        calibration_scores=calibration_scores,
        calibration_weights=calibration_weights,
        test_weights=test_weights,
        alpha=alpha,
    )
    if test_scores.shape != radii.shape:
        raise ValueError("Test scores and weights must be aligned")
    if not np.isfinite(test_scores).all() or (test_scores < 0).any():
        raise ValueError("Test scores must be finite and nonnegative")
    covered = test_scores <= radii
    finite_radii = radii[np.isfinite(radii)]
    cal_w = np.asarray(calibration_weights, dtype=np.float64)
    mean_w = float(cal_w.mean())
    coefficient = float(cal_w.std(ddof=0) / mean_w) if mean_w > 0 else float("inf")
    return ConformalEvaluation(
        successes=int(covered.sum()),
        trials=int(covered.size),
        coverage=float(covered.mean()),
        finite_radius_mean=float(finite_radii.mean()) if finite_radii.size else float("inf"),
        finite_radius_median=float(np.median(finite_radii)) if finite_radii.size else float("inf"),
        infinite_radius_rate=float(np.mean(~np.isfinite(radii))),
        effective_sample_size=float(effective_sample_size(cal_w)),
        max_calibration_weight=float(cal_w.max()),
        weight_coefficient_of_variation=coefficient,
    )
