import pytest

from scorito.model import tournament as tn


def test_advance_matrix_complementary_and_monotonic():
    elo = {"Strong": 2100.0, "Mid": 1800.0, "Weak": 1500.0}
    P = tn.advance_matrix(["Strong", "Mid", "Weak"], elo)
    # complementary
    assert P[("Strong", "Weak")] + P[("Weak", "Strong")] == pytest.approx(1.0)
    # stronger team advances more often; all in (0,1)
    assert P[("Strong", "Weak")] > P[("Mid", "Weak")] > 0.5
    assert 0.0 < P[("Weak", "Strong")] < 0.5
