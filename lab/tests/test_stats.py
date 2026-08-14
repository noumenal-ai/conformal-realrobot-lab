from ccwm_lab.stats import wilson_interval


def test_wilson_interval_contains_observed_fraction() -> None:
    interval = wilson_interval(90, 100, 0.95)
    assert interval.lower < 0.9 < interval.upper
    assert 0.0 <= interval.lower <= interval.upper <= 1.0
