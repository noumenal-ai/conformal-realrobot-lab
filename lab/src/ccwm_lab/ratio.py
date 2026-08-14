from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, xlogy
from scipy.stats import rankdata


@dataclass(frozen=True)
class LogisticFit:
    coefficients: tuple[float, ...]
    intercept: float
    success: bool
    status: int
    message: str
    iterations: int
    objective: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def empirical_midrank_unit(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("Midrank shift statistic requires a one-dimensional pool with at least two values")
    if not np.isfinite(values).all():
        raise ValueError("Shift input contains non-finite values")
    ranks = rankdata(values, method="average")
    return (2.0 * (ranks - 1.0) / (values.size - 1.0) - 1.0).astype(np.float64)


def exponential_tilt_laws(g: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    g = np.asarray(g, dtype=np.float64)
    if g.ndim != 1 or not np.isfinite(g).all():
        raise ValueError("g must be a finite vector")
    if np.max(np.abs(g)) > 1.0 + 1e-12:
        raise ValueError("Frozen shift statistic must lie in [-1,1]")

    log_p = -float(lam) * g
    log_q = +float(lam) * g
    log_p -= np.max(log_p)
    log_q -= np.max(log_q)
    p = np.exp(log_p)
    q = np.exp(log_q)
    p /= p.sum()
    q /= q.sum()
    w = q / p
    if not np.allclose(np.sum(p), 1.0) or not np.allclose(np.sum(q), 1.0):
        raise AssertionError("Tilt normalization failed")
    if not np.isfinite(w).all() or (w <= 0).any():
        raise AssertionError("Oracle ratio must be finite and strictly positive")
    return p, q, w


def posterior_from_ratio(w: np.ndarray, rho: float) -> np.ndarray:
    w = np.asarray(w, dtype=np.float64)
    if not (0.0 < rho < 1.0):
        raise ValueError("rho must lie in (0,1)")
    numerator = rho * w
    eta = numerator / ((1.0 - rho) + numerator)
    return eta


def ratio_from_posterior(h: np.ndarray, rho: float) -> np.ndarray:
    h = np.asarray(h, dtype=np.float64)
    if not (0.0 < rho < 1.0):
        raise ValueError("rho must lie in (0,1)")
    if (h <= 0).any() or (h >= 1).any():
        raise ValueError("Posterior probabilities must lie strictly in (0,1)")
    return ((1.0 - rho) / rho) * h / (1.0 - h)


def mixture_mass(p: np.ndarray, q: np.ndarray, rho: float) -> np.ndarray:
    return (1.0 - rho) * np.asarray(p, dtype=np.float64) + rho * np.asarray(q, dtype=np.float64)


def _design_matrix(g: np.ndarray) -> np.ndarray:
    g = np.asarray(g, dtype=np.float64).reshape(-1)
    return np.column_stack([np.ones(g.size, dtype=np.float64), g])


def fit_ridge_logistic(
    g: np.ndarray,
    labels: np.ndarray,
    *,
    ridge: float,
    max_iterations: int,
    tolerance: float,
) -> LogisticFit:
    g = np.asarray(g, dtype=np.float64).reshape(-1)
    y = np.asarray(labels, dtype=np.float64).reshape(-1)
    if g.shape != y.shape or g.size == 0:
        raise ValueError("Domain feature and label arrays must be nonempty and aligned")
    if not np.isin(y, [0.0, 1.0]).all():
        raise ValueError("Domain labels must be binary")
    if ridge < 0:
        raise ValueError("Ridge penalty must be nonnegative")
    x = _design_matrix(g)

    def objective(theta: np.ndarray) -> tuple[float, np.ndarray]:
        logits = x @ theta
        loss = np.mean(np.logaddexp(0.0, logits) - y * logits)
        penalty = 0.5 * ridge * float(np.dot(theta[1:], theta[1:]))
        probs = expit(logits)
        grad = (x.T @ (probs - y)) / y.size
        grad[1:] += ridge * theta[1:]
        return float(loss + penalty), grad

    result = minimize(
        fun=lambda theta: objective(theta)[0],
        x0=np.zeros(x.shape[1], dtype=np.float64),
        jac=lambda theta: objective(theta)[1],
        method="L-BFGS-B",
        options={"maxiter": int(max_iterations), "ftol": float(tolerance), "gtol": float(tolerance)},
    )
    fit = LogisticFit(
        coefficients=tuple(float(v) for v in result.x[1:]),
        intercept=float(result.x[0]),
        success=bool(result.success),
        status=int(result.status),
        message=str(result.message),
        iterations=int(result.nit),
        objective=float(result.fun),
    )
    if not fit.success:
        raise RuntimeError(f"Frozen logistic optimizer failed: {fit.message}")
    return fit


def predict_posterior(fit: LogisticFit, g: np.ndarray, gamma: float) -> np.ndarray:
    if not (0.0 < gamma < 0.5):
        raise ValueError("gamma must lie in (0,1/2)")
    g = np.asarray(g, dtype=np.float64).reshape(-1)
    beta = np.asarray(fit.coefficients, dtype=np.float64)
    if beta.shape != (1,):
        raise ValueError("Frozen classifier expects exactly one non-intercept feature")
    logits = fit.intercept + beta[0] * g
    return np.clip(expit(logits), gamma, 1.0 - gamma)


def bernoulli_kl(eta: np.ndarray, h: np.ndarray) -> np.ndarray:
    eta = np.asarray(eta, dtype=np.float64)
    h = np.asarray(h, dtype=np.float64)
    if eta.shape != h.shape:
        raise ValueError("eta and h must have the same shape")
    if (eta < 0).any() or (eta > 1).any() or (h <= 0).any() or (h >= 1).any():
        raise ValueError("Invalid Bernoulli probabilities")
    return xlogy(eta, eta / h) + xlogy(1.0 - eta, (1.0 - eta) / (1.0 - h))


def population_logistic_regret(m: np.ndarray, eta: np.ndarray, h: np.ndarray) -> float:
    m = np.asarray(m, dtype=np.float64)
    if not np.isclose(m.sum(), 1.0):
        raise ValueError("Mixture mass must sum to one")
    value = float(np.sum(m * bernoulli_kl(eta, h)))
    return max(0.0, value)


def l1_ratio_error(p: np.ndarray, w: np.ndarray, what: np.ndarray) -> float:
    return float(np.sum(np.asarray(p) * np.abs(np.asarray(w) - np.asarray(what))))


def normalized_surrogate(p: np.ndarray, v: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    if p.shape != v.shape or (p < 0).any() or (v < 0).any() or not np.isfinite(v).all():
        raise ValueError("Invalid source mass or surrogate weights")
    raw = p * v
    z = float(raw.sum())
    if not np.isfinite(z) or z <= 0:
        raise ValueError("Surrogate normalization must be positive and finite")
    return raw / z


def total_variation(q: np.ndarray, qhat: np.ndarray) -> float:
    q = np.asarray(q, dtype=np.float64)
    qhat = np.asarray(qhat, dtype=np.float64)
    return float(0.5 * np.sum(np.abs(q - qhat)))


def classifier_regret_l1_bound(regret: float, rho: float, gamma: float) -> float:
    if regret < 0 or not (0 < rho < 1) or not (0 < gamma < 0.5):
        raise ValueError("Invalid theorem-bound inputs")
    return float(np.sqrt(regret / 2.0) / (rho * gamma))


def posterior_ratio_identity_lhs_rhs(
    p: np.ndarray,
    q: np.ndarray,
    eta: np.ndarray,
    h: np.ndarray,
    rho: float,
) -> tuple[float, float]:
    w = np.asarray(q) / np.asarray(p)
    what = ratio_from_posterior(h, rho)
    lhs = l1_ratio_error(p, w, what)
    m = mixture_mass(p, q, rho)
    rhs = float((1.0 / rho) * np.sum(m * np.abs(eta - h) / (1.0 - h)))
    return lhs, rhs
