"""Knockout-phase logic: KO scoring (90/60 XOR), realized-form blend, ET grid,
single-game topscorer multipliers, alive/injury filter."""
import numpy as np
import pytest

from scorito import config
from scorito import knockout as ko
from scorito.eval import metrics
from scorito.model.grid import build_grid
from scorito.model.match_ev import score_ev
from scorito.model.topscorers import build_expected_goals, score_candidate
from scorito.types import Match


# --- KO match EV: exact pays 90 (not 150), toto 60, XOR decomposition ---
def test_score_ev_knockout_xor_decomposition():
    grid = build_grid(1.6, 0.8)
    ev = score_ev(grid, 1, 0, pts_exact=90, pts_toto=60)
    assert ev == pytest.approx((90 - 60) * grid.exact(1, 0) + 60 * grid.p_home)


def test_score_ev_defaults_to_group_constants():
    grid = build_grid(1.6, 0.8)
    assert score_ev(grid, 1, 0) == pytest.approx(
        (config.PTS_EXACT - config.PTS_TOTO) * grid.exact(1, 0) + config.PTS_TOTO * grid.p_home)


# --- realized KO scoring for grading future rounds ---
def test_match_points_knockout_scoring():
    assert metrics.match_points((2, 1), (2, 1), pts_exact=90, pts_toto=60) == 90
    assert metrics.match_points((1, 0), (2, 1), pts_exact=90, pts_toto=60) == 60  # both home wins
    assert metrics.match_points((1, 0), (0, 1), pts_exact=90, pts_toto=60) == 0
    assert metrics.match_points((2, 1), (2, 1)) == config.PTS_EXACT  # group default unchanged


# --- realized-form blend (retro fix: weight tournament goals) ---
def test_blend_g90_lifts_hot_scorer_and_shrinks_cold():
    hot = ko.blend_g90(0.55, tourn_nonpen_goals=6, games=3, prior_games=6)
    cold = ko.blend_g90(0.23, tourn_nonpen_goals=0, games=3, prior_games=6)
    assert hot == pytest.approx((6 * 0.55 + 6) / 9)
    assert cold == pytest.approx((6 * 0.23 + 0) / 9)
    assert hot > 0.55 and cold < 0.23


def test_blend_g90_no_games_returns_club():
    assert ko.blend_g90(0.4, 0, games=0, prior_games=6) == pytest.approx(0.4)


# --- single-game topscorer EV with KO multipliers (16/32/64/64) ---
def test_score_candidate_knockout_multiplier():
    att = {"position": "ATT", "exp_goals": 0.5}
    deff = {"position": "DEF", "exp_goals": 0.13}
    assert score_candidate(att, {}, mult=config.KO_TOPSCORER_MULT) == pytest.approx(0.5 * 16)
    assert score_candidate(deff, {}, mult=config.KO_TOPSCORER_MULT) == pytest.approx(0.13 * 64)


def test_build_expected_goals_single_game_pen_bonus():
    c = [{"name": "X", "team": "A", "position": "ATT", "g90": 0.0,
          "start_prob": 1.0, "pen_taker": True, "pen_share": 1.0}]
    out = build_expected_goals(c, [Match("A", "B", "R32")], atgs_map={},
                               team_factors={"A": 1.0, "B": 1.0}, pen_bonus=0.06)
    assert out[0]["exp_goals"] == pytest.approx(0.06)  # g90 term 0 + single-game pen bonus


def test_build_expected_goals_goal_term_is_single_game_not_triple():
    # The hand-fallback goal term must be g90*1 (one knockout game), NOT g90*3 (the group default).
    # Non-zero g90 + no penalty isolates the goal term (regression guard for a *3 leak).
    c = [{"name": "Y", "team": "A", "position": "ATT", "g90": 0.5, "start_prob": 1.0, "pen_taker": False}]
    out = build_expected_goals(c, [Match("A", "B", "R32")], atgs_map={},
                               team_factors={"A": 1.0, "B": 1.0}, pen_bonus=0.07)
    assert out[0]["exp_goals"] == pytest.approx(0.5)  # 0.5*1*1, not 1.5


# --- extra-time uplift: "stand na 120 min" -> more goals, fewer draws ---
def _exp_total(g):
    n = g.matrix.shape[0]
    return float(sum((i + j) * g.matrix[i, j] for i in range(n) for j in range(n)))


def test_et_grid_raises_total_and_lowers_draw():
    g90 = build_grid(1.3, 1.3)
    g_et = ko.et_adjusted_grid(1.3, 1.3)
    assert _exp_total(g_et) > _exp_total(g90)
    assert g_et.p_draw < g90.p_draw


# --- alive + injury filter ---
def test_filter_alive_drops_eliminated_and_injured():
    cands = [{"name": "Federico Valverde", "team": "Uruguay"},
             {"name": "Raphinha", "team": "Brazil"},
             {"name": "Harry Kane", "team": "England"}]
    kept = ko.filter_alive(cands, alive_teams={"England", "Brazil", "Argentina"},
                           injured_out={"Raphinha"})
    assert {c["name"] for c in kept} == {"Harry Kane"}
