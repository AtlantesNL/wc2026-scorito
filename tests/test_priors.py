import pytest

from scorito.data.priors import blend_champion_probs


def test_blend_weight_zero_is_pure_mc():
    mc = {"A": 0.5, "B": 0.3, "C": 0.2}
    out = blend_champion_probs(mc, {"A": 0.9}, weight=0.0)
    assert out == pytest.approx(mc)


def test_blend_sums_to_one_and_pulls_toward_market():
    mc = {"A": 0.2, "B": 0.2, "C": 0.6}
    market = {"A": 0.5}                       # only A covered (sums 0.5 < 1)
    out = blend_champion_probs(mc, market, weight=1.0)  # market_full only
    assert sum(out.values()) == pytest.approx(1.0)
    # A gets its market prob; B,C split the 0.5 residual in proportion to mc (0.2:0.6)
    assert out["A"] == pytest.approx(0.5)
    assert out["B"] == pytest.approx(0.5 * 0.2 / 0.8)
    assert out["C"] == pytest.approx(0.5 * 0.6 / 0.8)


def test_blend_half_and_half_sums_to_one():
    mc = {"A": 0.2, "B": 0.2, "C": 0.6}
    out = blend_champion_probs(mc, {"A": 0.5}, weight=0.5)
    assert sum(out.values()) == pytest.approx(1.0)
    assert out["A"] == pytest.approx(0.5 * 0.5 + 0.5 * 0.2)


def test_market_anchors_include_argentina_and_lower_its_prior():
    from scorito.data.priors import MARKET, OPTA, blended_probs
    assert {"Spain", "France", "England", "Argentina", "Brazil"} <= set(MARKET)
    b = blended_probs()
    assert b["Argentina"] < OPTA["Argentina"]      # the ~8% market anchor pulls Argentina down
    assert b["Germany"] == OPTA["Germany"]         # uncovered team still uses Opta unchanged
