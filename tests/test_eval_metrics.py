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


def test_match_points_exact_toto_miss():
    assert metrics.match_points((1, 0), (1, 0)) == 45   # exact
    assert metrics.match_points((2, 1), (1, 0)) == 30   # right home win, wrong score
    assert metrics.match_points((1, 1), (1, 0)) == 0    # wrong outcome
    assert metrics.match_points((0, 0), (2, 2)) == 30   # both draws, wrong score


def test_standings_points_counts_correct_positions():
    assert metrics.standings_points(["A", "B", "C", "D"], ["A", "C", "B", "D"]) == 50  # A,D right


def test_topscorer_points_uses_position_multiplier():
    picks = [dict(name="Kane", position="ATT"), dict(name="Hakimi", position="DEF")]
    goals = {"Kane": 3, "Hakimi": 1}
    assert metrics.topscorer_points(picks, goals) == 3 * 8 + 1 * 32
