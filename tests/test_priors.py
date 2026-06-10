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


def test_blend_renormalizes_when_market_covers_all_mc_teams():
    # Live consensus lists every MC team but its covered mass is <1 (non-qualified "ghost"
    # teams hold the rest). The market component must be renormalized to 1, not leak the
    # residual (which made blended probs sum to ~0.985 and understate every P(win)).
    mc = {"A": 0.5, "B": 0.3, "C": 0.2}
    market = {"A": 0.30, "B": 0.20, "C": 0.10}      # covers all of mc, sums to only 0.60
    out = blend_champion_probs(mc, market, weight=0.5)
    assert sum(out.values()) == pytest.approx(1.0)
    # market renormalized A:0.30/0.60=0.5; blended 50/50 with mc's 0.5 -> 0.5
    assert out["A"] == pytest.approx(0.5 * 0.5 + 0.5 * 0.5)


def test_market_anchors_include_argentina_and_lower_its_prior():
    from scorito.data.priors import MARKET, OPTA, blended_probs
    assert {"Spain", "France", "England", "Portugal", "Argentina", "Brazil",
            "Germany", "Netherlands"} <= set(MARKET)
    b = blended_probs()
    assert b["Argentina"] < OPTA["Argentina"]      # the ~8% market anchor pulls Argentina down
    assert b["Portugal"] > OPTA["Portugal"]        # the 10% anchor lifts Portugal (Opta under-rated it)
    assert b["Mexico"] == OPTA["Mexico"]           # uncovered team still uses Opta unchanged


def test_blended_probs_uses_live_market_and_includes_market_only_teams():
    from scorito.data.priors import blended_probs, OPTA
    live = {"Spain": 0.16, "Morocco": 0.03}        # Spain is in Opta; Morocco is market-only
    b = blended_probs(market=live)
    assert b["Spain"] == pytest.approx(0.5 * OPTA["Spain"] + 0.5 * 0.16)
    assert b["Morocco"] == pytest.approx(0.03)      # market-only team included at its market prob
    assert b["Argentina"] == OPTA["Argentina"]      # not in the live market -> Opta only
    assert blended_probs()["England"] == pytest.approx(0.5 * OPTA["England"] + 0.5 * 0.11)  # no-arg fallback unchanged
