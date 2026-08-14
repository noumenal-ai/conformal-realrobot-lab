import numpy as np

from ccwm_lab.ratio import empirical_midrank_unit


def test_midrank_is_bounded_and_monotone() -> None:
    values = np.array([3.0, 1.0, 2.0, 2.0])
    g = empirical_midrank_unit(values)
    assert np.max(np.abs(g)) <= 1.0
    assert g[1] < g[2] == g[3] < g[0]
