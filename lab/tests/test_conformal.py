import numpy as np

from ccwm_lab.conformal import effective_sample_size, weighted_conformal_radii


def test_plus_infinity_atom_is_test_weight_dependent() -> None:
    scores = np.array([1.0, 2.0, 3.0])
    weights = np.ones(3)
    radii = weighted_conformal_radii(scores, weights, np.array([0.1, 100.0]), alpha=0.1)
    assert radii[0] == 3.0
    assert np.isinf(radii[1])


def test_effective_sample_size() -> None:
    assert np.isclose(effective_sample_size(np.ones(5)), 5.0)
    assert effective_sample_size(np.array([1.0, 0.0, 0.0])) == 1.0
