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


from scorito.model.bracket import KOMatch, GroupPos
from scorito.model.grid import build_grid


def _toy():
    # two groups of 3; in each the "fav" (home/first team) gets dominant scoring grids
    gteams = {"A": ["AA", "AB", "AC"], "B": ["BA", "BB", "BC"]}
    matches = [("AA", "AB"), ("AA", "AC"), ("AB", "AC"),
               ("BA", "BB"), ("BA", "BC"), ("BB", "BC")]
    strong = build_grid(2.6, 0.2)   # home wins big
    even = build_grid(1.0, 1.0)
    grids = {("AA", "AB"): strong, ("AA", "AC"): strong, ("AB", "AC"): even,
             ("BA", "BB"): strong, ("BA", "BC"): strong, ("BB", "BC"): even}
    # AA and BA win their groups; AA hugely stronger by Elo -> wins the final
    elo = {"AA": 2400, "AB": 1500, "AC": 1500, "BA": 1700, "BB": 1500, "BC": 1500}
    bracket = [KOMatch(num=1, round="Final", team1=GroupPos(1, "A"), team2=GroupPos(1, "B"))]
    return gteams, matches, grids, elo, bracket


def test_simulate_probs_sum_to_one_and_favor_strongest():
    gteams, matches, grids, elo, bracket = _toy()
    out = tn.simulate(gteams, matches, grids, elo, bracket, sims=2000, seed=1)
    assert sum(out["win"].values()) == pytest.approx(1.0, abs=1e-9)
    assert out["win"]["AA"] > 0.6                 # dominant team usually champion
    assert out["win"]["AA"] == max(out["win"].values())


def test_simulate_is_seed_deterministic():
    gteams, matches, grids, elo, bracket = _toy()
    a = tn.simulate(gteams, matches, grids, elo, bracket, sims=500, seed=7)
    b = tn.simulate(gteams, matches, grids, elo, bracket, sims=500, seed=7)
    assert a["win"] == b["win"]


def test_simulate_with_real_bracket_covers_all_48():
    import itertools
    from scorito.model.bracket import load_bracket
    brk = load_bracket("data/cache/worldcup2026.json")
    groups = "ABCDEFGHIJKL"
    gteams = {g: [f"{g}{i}" for i in range(1, 5)] for g in groups}
    even = build_grid(1.3, 1.1)
    group_matches, grids = [], {}
    for g in groups:
        for a, b in itertools.combinations(gteams[g], 2):
            group_matches.append((a, b))
            grids[(a, b)] = even
    elo = {f"{g}{i}": 1500.0 for g in groups for i in range(1, 5)}
    out = tn.simulate(gteams, group_matches, grids, elo, brk, sims=300, seed=3)
    assert len(out["win"]) == 48
    assert sum(out["win"].values()) == pytest.approx(1.0, abs=1e-9)
    assert all(0.0 <= p <= 1.0 for p in out["win"].values())
