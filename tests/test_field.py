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
