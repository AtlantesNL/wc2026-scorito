import numpy as np

from scorito.model.grid import build_grid
from scorito.model.group_sim import _rank_table, position_probs

TEAMS = ["A", "B", "C", "D"]
MATCHES = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]


def test_position_probs_sum_to_one():
    grids = {m: build_grid(1.3, 1.3) for m in MATCHES}  # fully symmetric group
    probs = position_probs(TEAMS, MATCHES, grids, sims=2000, seed=1)
    for t in TEAMS:
        assert abs(probs[t].sum() - 1.0) < 1e-9
    assert abs(probs["A"][0] - 0.25) < 0.06  # symmetric -> ~25% to win


def test_stronger_team_wins_group_more_often():
    grids = dict.fromkeys(MATCHES)
    for (a, b) in MATCHES:
        # A is strong, others even
        lam = (2.1, 0.7) if a == "A" else (0.7, 2.1) if b == "A" else (1.3, 1.3)
        grids[(a, b)] = build_grid(*lam)
    probs = position_probs(TEAMS, MATCHES, grids, sims=3000, seed=2)
    assert probs["A"][0] > 0.5  # strong team tops the group most often


def test_rank_table_primary_key():
    stats = {
        "A": dict(pts=6, gd=4, gf=5),
        "B": dict(pts=6, gd=2, gf=4),
        "C": dict(pts=3, gd=-2, gf=2),
        "D": dict(pts=0, gd=-4, gf=1),
    }
    order = _rank_table(stats, h2h=None, rng=np.random.default_rng(0))
    assert order[0] == "A" and order[1] == "B" and order[-1] == "D"


def test_rank_table_head_to_head_breaks_tie():
    # A and B identical on (pts, gd, gf); A beat B head-to-head -> A above B
    stats = {
        "A": dict(pts=6, gd=1, gf=2),
        "B": dict(pts=6, gd=1, gf=2),
        "C": dict(pts=3, gd=0, gf=2),
        "D": dict(pts=0, gd=-2, gf=1),
    }
    h2h = {("A", "B"): (1, 0), ("C", "D"): (2, 1)}
    order = _rank_table(stats, h2h=h2h, rng=np.random.default_rng(0))
    assert order[0] == "A" and order[1] == "B"


def test_rank_table_deterministic_without_rng():
    stats = {"A": dict(pts=3, gd=0, gf=1), "B": dict(pts=3, gd=0, gf=1)}
    o1 = _rank_table(dict(stats), h2h=None, rng=None)
    o2 = _rank_table(dict(stats), h2h=None, rng=None)
    assert o1 == o2 and set(o1) == {"A", "B"}
