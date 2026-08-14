import numpy as np

from ccwm_lab.ratio import (
    classifier_regret_l1_bound,
    exponential_tilt_laws,
    l1_ratio_error,
    mixture_mass,
    population_logistic_regret,
    posterior_from_ratio,
    posterior_ratio_identity_lhs_rhs,
    ratio_from_posterior,
)


def test_exact_posterior_ratio_identity_and_bound() -> None:
    g = np.array([-1.0, -0.25, 0.4, 1.0])
    p, q, w = exponential_tilt_laws(g, 0.8)
    rho = 0.5
    gamma = 0.05
    eta = posterior_from_ratio(w, rho)
    h = np.clip(0.9 * eta + 0.05, gamma, 1.0 - gamma)
    what = ratio_from_posterior(h, rho)
    lhs, rhs = posterior_ratio_identity_lhs_rhs(p, q, eta, h, rho)
    assert np.isclose(lhs, rhs, rtol=1e-12, atol=1e-12)
    regret = population_logistic_regret(mixture_mass(p, q, rho), eta, h)
    bound = classifier_regret_l1_bound(regret, rho, gamma)
    assert l1_ratio_error(p, w, what) <= bound + 1e-12


def test_oracle_ratio_integrates_to_one() -> None:
    p, q, w = exponential_tilt_laws(np.array([-1.0, 0.0, 1.0]), 1.2)
    assert np.isclose(np.sum(p * w), 1.0)
    assert np.allclose(p * w, q)
