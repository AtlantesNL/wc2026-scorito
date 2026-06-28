import itertools

import numpy as np
import pytest

from scorito.model import pool
from scorito.model.bracket import load_bracket
from scorito.model.grid import build_grid


def _world_inputs():
    groups = "ABCDEFGHIJKL"
    gteams = {g: [f"{g}{i}" for i in range(1, 5)] for g in groups}
    even = build_grid(1.3, 1.1)
    group_matches, grids = [], {}
    for g in groups:
        for a, b in itertools.combinations(gteams[g], 2):
            group_matches.append((a, b))
            grids[(a, b)] = even
    elo = {f"{g}{i}": 1500.0 for g in groups for i in range(1, 5)}
    cands = [dict(name="A1", team="A1", position="ATT", g90=0.6, start_prob=1.0, pen_taker=False)]
    bracket = load_bracket("data/worldcup2026_fixtures.json")
    return gteams, group_matches, grids, elo, bracket, cands


def test_sample_worlds_shape_and_content():
    gteams, gm, grids, elo, bracket, cands = _world_inputs()
    worlds = pool.sample_worlds(gteams, gm, grids, elo, bracket, cands,
                                team_factors={}, sims=200, seed=0)
    assert len(worlds) == 200
    w = worlds[0]
    assert set(w) == {"scores", "place", "champion", "pgoals"}
    assert len(w["scores"]) == 72 and len(w["place"]) == 12
    assert w["champion"] in {f"{g}{i}" for g in gteams for i in range(1, 5)}
    assert w["pgoals"]["A1"] >= 0


def test_champion_win_probs_no_field_is_one():
    probs = pool.champion_win_probs(np.zeros(10), np.zeros((0, 10)),
                                    [], np.array(["X"] * 10, dtype=object), ["X"])
    assert probs["X"] == 1.0


def test_champion_win_probs_brute_equivalence():
    rng = np.random.default_rng(0)
    W, N = 500, 4
    champ_w = np.array(rng.choice(["X", "Y"], W), dtype=object)
    base_w = rng.normal(1000, 10, W)
    rival_base = rng.normal(1000, 10, (N, W))
    rival_champ = ["X", "Y", "X", "Y"]
    fast = pool.champion_win_probs(base_w, rival_base, rival_champ, champ_w, ["X", "Y"])
    wins = 0
    for w in range(W):
        ours = base_w[w] + 250 * (champ_w[w] == "Y")
        rivals = [rival_base[r, w] + 250 * (rival_champ[r] == champ_w[w]) for r in range(N)]
        wins += ours > max(rivals)
    assert abs(fast["Y"] - wins / W) < 1e-9


def test_champion_win_probs_leverage_off_overowned_favourite():
    # whole field on favourite X; X champions 60% of worlds, Y 40%; bases ~equal.
    rng = np.random.default_rng(0)
    W, N = 4000, 25
    champ_w = np.where(rng.random(W) < 0.6, "X", "Y").astype(object)
    base_w = rng.normal(1000, 5, W)
    rival_base = rng.normal(1000, 5, (N, W))
    rival_champ = ["X"] * N
    probs = pool.champion_win_probs(base_w, rival_base, rival_champ, champ_w, ["X", "Y"])
    assert probs["Y"] > probs["X"]          # core thesis: leverage off the crowd
    assert 0 <= probs["X"] <= 1 and 0 <= probs["Y"] <= 1


def test_best_with_floor_breaks_near_ties_toward_higher_outright():
    win = {"Portugal": 0.068, "Argentina": 0.064, "Colombia": 0.058}
    outright = {"Portugal": 0.060, "Argentina": 0.118, "Colombia": 0.042}
    # within eps: Portugal & Argentina tie on win-pool -> prefer the higher-floor Argentina
    assert pool._best_with_floor(win, outright, eps=0.005) == "Argentina"
    # eps=0 -> strict argmax of win-pool
    assert pool._best_with_floor(win, outright, eps=0.0) == "Portugal"


def test_greedy_topscorers_picks_underowned_high_variance():
    our_fixed = np.array([8.0, 8, 8, 8])
    max_rival = np.array([10.0, 10, 10, 10])
    points = {
        "striker": np.array([1.0, 1, 1, 1]),   # always +1 -> 9 < 10, never wins (commoditized)
        "defender": np.array([0.0, 0, 0, 5]),   # spikes in world 4 -> 13 > 10 there
    }
    names, pwin = pool.greedy_topscorers(our_fixed, max_rival, points, n_slots=1)
    assert names == ["defender"] and abs(pwin - 0.25) < 1e-9


def test_greedy_topscorers_no_field_reduces_to_ev():
    our_fixed = np.zeros(4)
    max_rival = np.full(4, -np.inf)            # no rivals -> every pick wins; tie-break by EV
    points = {"lo": np.array([1.0, 1, 1, 1]), "hi": np.array([2.0, 2, 2, 2])}
    names, pwin = pool.greedy_topscorers(our_fixed, max_rival, points, n_slots=1)
    assert names == ["hi"] and pwin == 1.0


def test_pool_win_champion_default_sharpnesses_are_realistic():
    import inspect
    sweep = inspect.signature(pool.pool_win_champion).parameters["sharpnesses"].default
    assert all(s <= 2.0 for s in sweep) and min(sweep) <= 1.0   # plausible amateur dispersions only
