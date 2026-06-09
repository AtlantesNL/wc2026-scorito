import numpy as np

from scorito.model import field as fld


def _inputs():
    champion_probs = {"Fav": 0.5, "Mid": 0.3, "Long": 0.2}
    scoreline_choices = {("A", "B"): [((1, 0), 0.6), ((2, 1), 0.3), ((0, 0), 0.1)]}
    topscorer_pool = [(dict(name=f"P{i}", team="A", position="ATT"), ev)
                      for i, ev in enumerate([30, 20, 15, 10, 8, 6, 4, 2])]
    return champion_probs, scoreline_choices, topscorer_pool


def test_chalky_field_concentrates_on_favourite():
    cp, sc, ts = _inputs()
    rng = np.random.default_rng(0)
    entries = fld.generate_field(400, sc, cp, ts, sharpness=3.0, rng=rng)
    assert len(entries) == 400
    champs = [e["champion"] for e in entries]
    assert champs.count("Fav") / 400 > 0.6   # chalky -> Fav above its raw 0.5 share
    e = entries[0]
    assert set(e) == {"scorelines", "champion", "topscorers"}
    assert e["scorelines"][("A", "B")] in [(1, 0), (2, 1), (0, 0)]
    assert len(e["topscorers"]) == 6 and len({t["name"] for t in e["topscorers"]}) == 6


def test_sharpness_zero_is_near_uniform_champion():
    cp, sc, ts = _inputs()
    rng = np.random.default_rng(1)
    entries = fld.generate_field(600, sc, cp, ts, sharpness=0.0, rng=rng)
    share = [e["champion"] for e in entries].count("Fav") / 600
    assert 0.25 < share < 0.40   # ~1/3 uniform across the 3 teams


def test_field_is_seed_deterministic():
    cp, sc, ts = _inputs()
    a = fld.generate_field(50, sc, cp, ts, 2.0, np.random.default_rng(7))
    b = fld.generate_field(50, sc, cp, ts, 2.0, np.random.default_rng(7))
    assert [e["champion"] for e in a] == [e["champion"] for e in b]


def test_scoreline_ownership_downweights_draws_and_sums_to_one():
    from scorito.model.grid import ScoreGrid
    m = np.zeros((3, 3)); m[1, 0] = 0.4; m[1, 1] = 0.3; m[0, 0] = 0.1; m[2, 1] = 0.2
    g = ScoreGrid(m, p_home=0.6, p_draw=0.4, p_away=0.0)   # draws (1-1,0-0) = 0.4 of the grid
    oe, ot = fld.scoreline_ownership(g, draw_aversion=0.4, sharpness=1.0)
    assert abs(sum(oe.values()) - 1.0) < 1e-9
    assert abs(ot["home"] + ot["draw"] + ot["away"] - 1.0) < 1e-9
    assert ot["draw"] < 0.4                                # draws down-weighted below grid share
    oe2, ot2 = fld.scoreline_ownership(g, draw_aversion=1.0, sharpness=1.0)
    assert abs(ot2["draw"] - 0.4) < 1e-9                   # aversion=1 -> raw grid share


def test_fame_weighted_field_overowns_attackers():
    from scorito.model.topscorers import fame_score
    cp = {"X": 1.0}
    sc = {("A", "B"): [((1, 0), 1.0)]}
    tf = {"T": 1.0}
    att = dict(name="Att", team="T", position="ATT", g90=0.5, start_prob=1.0)
    dfn = dict(name="Def", team="T", position="DEF", g90=0.125, start_prob=1.0)  # equal EV to Att
    fillers = [dict(name=f"F{i}", team="T", position="ATT", g90=0.1, start_prob=1.0) for i in range(8)]
    cands = [att, dfn] + fillers
    ts_pool = [(c, fame_score(c, tf)) for c in cands]
    entries = fld.generate_field(500, sc, cp, ts_pool, sharpness=2.0, rng=np.random.default_rng(0))
    own = lambda nm: sum(1 for e in entries if any(t["name"] == nm for t in e["topscorers"]))
    assert own("Att") > own("Def")     # equal Scorito EV, but fame over-owns the attacker
