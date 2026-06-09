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
    bracket = load_bracket("data/cache/worldcup2026.json")
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
