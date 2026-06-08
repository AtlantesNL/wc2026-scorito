import math

import pytest

from scorito.eval import metrics


def test_log_loss_perfect_and_clamped():
    assert metrics.log_loss([1.0, 0.0, 0.0], 0) == pytest.approx(0.0, abs=1e-9)
    # clamped: never infinite even if prob is 0
    assert 30 < metrics.log_loss([0.0, 1.0, 0.0], 0) < 40


def test_log_loss_known_value():
    assert metrics.log_loss([0.5, 0.3, 0.2], 1) == pytest.approx(-math.log(0.3), abs=1e-9)


def test_brier_known_value():
    # outcome idx 0: (0.7-1)^2 + (0.2-0)^2 + (0.1-0)^2 = 0.09+0.04+0.01 = 0.14
    assert metrics.brier([0.7, 0.2, 0.1], 0) == pytest.approx(0.14, abs=1e-9)


def test_reliability_bins_groups_by_predicted():
    pairs = [(0.05, False), (0.05, False), (0.95, True), (0.95, True)]
    bins = metrics.reliability_bins(pairs, nbins=10)
    assert bins[0] == (pytest.approx(0.05), pytest.approx(0.0), 2)
    assert bins[9] == (pytest.approx(0.95), pytest.approx(1.0), 2)
    assert bins[5] == (None, None, 0)
