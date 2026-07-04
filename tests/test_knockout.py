"""Knockout-phase logic: KO scoring (90/60 XOR), realized-form blend, ET grid,
single-game topscorer multipliers, alive/injury filter."""
import math

import numpy as np
import pytest

from scorito import config
from scorito import knockout as ko
from scorito.eval import metrics
from scorito.model.grid import build_grid
from scorito.model.match_ev import score_ev
from scorito.model.topscorers import build_expected_goals, score_candidate, shrink_mult
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


# --- brace de-bias: single-game per-goal EV over-credits multi-goal games for high-multiplier
#     MIDs (Poisson tail). ATT-only brace credit keeps strikers on full E[goals], scores others on
#     P(>=1). Default (no brace_credit) stays E[goals]*mult so R32 output is byte-identical. ---
def test_score_candidate_brace_credit_default_is_full_per_goal():
    mid = {"position": "MID", "exp_goals": 0.5}
    assert score_candidate(mid, {}, mult=config.KO_TOPSCORER_MULT) == pytest.approx(0.5 * 32)


def test_score_candidate_brace_de_bias_credits_braces_att_only():
    lam = 0.6
    mult = config.KO_ROUND_SCORING["Round of 16"]["mult"]
    bc = config.KO_BRACE_CREDIT
    att = {"position": "ATT", "exp_goals": lam}
    mid = {"position": "MID", "exp_goals": lam}
    p1 = 1.0 - math.exp(-lam)
    assert score_candidate(att, {}, mult=mult, brace_credit=bc) == pytest.approx(lam * mult["ATT"])
    assert score_candidate(mid, {}, mult=mult, brace_credit=bc) == pytest.approx(p1 * mult["MID"])
    assert score_candidate(mid, {}, mult=mult, brace_credit=bc) < lam * mult["MID"]


def test_score_candidate_brace_de_bias_demotes_inflated_mid_below_att():
    # A high-volume MID that outranks a star ATT under raw Poisson should flip under the de-bias.
    mult = config.KO_ROUND_SCORING["Round of 16"]["mult"]
    bc = config.KO_BRACE_CREDIT
    mid = {"position": "MID", "exp_goals": 0.45}   # 0.45*48 = 21.6 raw
    att = {"position": "ATT", "exp_goals": 0.80}   # 0.80*24 = 19.2 raw  -> MID wins raw
    assert score_candidate(mid, {}, mult=mult) > score_candidate(att, {}, mult=mult)
    assert (score_candidate(att, {}, mult=mult, brace_credit=bc)
            > score_candidate(mid, {}, mult=mult, brace_credit=bc))  # ATT wins de-biased


# --- lead-protection tilt: compress the per-goal multiplier toward the attacker multiplier so a
#     leader mirrors the attacker-heavy chalk field instead of chasing under-owned DEF/MID differentials.
def test_shrink_mult_compresses_toward_attacker():
    m = {"GK": 96, "DEF": 96, "MID": 48, "ATT": 24}
    assert shrink_mult(m, 1.0) == m                              # shrink 1 = no-op (pure EV)
    assert all(v == 24 for v in shrink_mult(m, 0.0).values())    # shrink 0 = position-blind (chalk)
    h = shrink_mult(m, 0.5)
    assert h["ATT"] == 24
    assert h["MID"] == pytest.approx(24 * (48 / 24) ** 0.5)      # ~33.9
    assert h["DEF"] == pytest.approx(24 * (96 / 24) ** 0.5)      # 48


def test_lead_protection_tilt_demotes_under_owned_differential():
    m = {"GK": 96, "DEF": 96, "MID": 48, "ATT": 24}
    bc = config.KO_BRACE_CREDIT
    att = {"position": "ATT", "exp_goals": 0.55}     # chalk striker
    deff = {"position": "DEF", "exp_goals": 0.16}    # set-piece longshot, high multiplier
    # Pure EV: the high-multiplier DEF outranks the striker (the Hakimi problem).
    assert (score_candidate(deff, {}, mult=m, brace_credit=bc)
            > score_candidate(att, {}, mult=m, brace_credit=bc))
    # Lead-protection tilt (shrink 0.5): the chalk striker outranks the differential DEF.
    sm = shrink_mult(m, 0.5)
    assert (score_candidate(att, {}, mult=sm, brace_credit=bc)
            > score_candidate(deff, {}, mult=sm, brace_credit=bc))


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
def test_best_scoreline_scales_linearly_with_round_points():
    # Ratios are identical (135/90 = 1.5 * 90/60) so the modal cell is unchanged and EV scales 1.5x.
    grid = build_grid(1.7, 0.7)
    h32, a32, ev32 = ko.best_scoreline(grid, pts_exact=90, pts_toto=60)
    h16, a16, ev16 = ko.best_scoreline(grid, pts_exact=135, pts_toto=90)
    assert (h16, a16) == (h32, a32)
    assert ev16 == pytest.approx(1.5 * ev32)


def test_lead_dashboard_reports_gap_and_swings():
    from scorito.data.knockout_fixtures import STANDINGS
    dash = ko.lead_dashboard(STANDINGS, config.KO_ROUND_SCORING["Round of 16"])
    for r in STANDINGS["rivals"]:            # gap line per rival, derived from the live data
        assert f"+{STANDINGS['you'] - r['points']}" in dash
    assert "45" in dash                       # exact-minus-toto swing 135-90
    assert "96" in dash                       # DEF/GK per-goal swing


def test_run_knockout_r16_end_to_end_offline(tmp_path):
    from scorito.data import knockout_fixtures as kf
    r = ko.run_knockout(ties=kf.R16_TIES, alive_teams=kf.R16_ALIVE_TEAMS,
                        injured_out=kf.R16_INJURED_OUT, start_overrides=kf.R16_START_OVERRIDES,
                        tie_notes=kf.R16_TIE_NOTES, round_name="Round of 16", out_dir=str(tmp_path))
    assert len(r["match_picks"]) == 8 and len(r["top4"]) == 4
    report = (tmp_path / "report.md").read_text()
    assert "Round of 16" in report
    assert "135" in report and "90" in report          # R16 scoring header
    assert (tmp_path / "picks.csv").exists()


def test_r16_fixtures_wellformed():
    from scorito.data.knockout_fixtures import R16_ALIVE_TEAMS, R16_TIES
    assert len(R16_TIES) == 8
    teams = {t for m in R16_TIES for t in (m.team1, m.team2)}
    assert len(teams) == 16
    assert teams == set(R16_ALIVE_TEAMS)
    for known in ("France", "Spain", "Portugal", "Brazil", "England", "Mexico", "Belgium", "USA"):
        assert known in R16_ALIVE_TEAMS


def test_all_r16_teams_have_a_topscorer_candidate():
    # The engine can only pick a scorer it knows about; every R16 team needs >=1 candidate so a
    # market-priced striker (e.g. Salah, Luis Díaz) is considered under tomorrow's ATGS odds.
    from scorito.data.knockout_fixtures import R16_ALIVE_TEAMS
    from scorito.data.topscorer_candidates import CANDIDATES
    teams_with = {c["team"] for c in CANDIDATES}
    assert set(R16_ALIVE_TEAMS) <= teams_with


def test_filter_alive_drops_eliminated_and_injured():
    cands = [{"name": "Federico Valverde", "team": "Uruguay"},
             {"name": "Raphinha", "team": "Brazil"},
             {"name": "Harry Kane", "team": "England"}]
    kept = ko.filter_alive(cands, alive_teams={"England", "Brazil", "Argentina"},
                           injured_out={"Raphinha"})
    assert {c["name"] for c in kept} == {"Harry Kane"}
