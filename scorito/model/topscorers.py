"""Topscorer EV model.

EV = (expected group-phase goals) * team_attack_factor * position_multiplier
where expected goals ~= g90 * 3 games * start_prob (+ a penalty bonus scaled by the
player's share of his team's penalties), and the per-goal multiplier (GK/DEF=32,
MID=16, ATT=8; ratio 4:2:1) makes high-volume MIDFIELDERS and any set-piece DEFENDER
disproportionately valuable. ``team_attack_factor`` (from the goals model) scales by
how much the player's side is expected to score across its three group games.

``pen_share`` (per candidate) is the fraction of his nation's penalties he takes; it
defaults to 1.0 for a flagged first-choice ``pen_taker`` and 0.0 otherwise, so a
co-/second-choice taker can be modelled at e.g. 0.5 rather than all-or-nothing.
"""
import numpy as np

from scorito import config
from scorito.data.topscorer_candidates import CANDIDATES

PEN_BONUS = 0.20  # extra expected group-phase goals for a side's *sole* penalty taker


def score_candidate(c, team_factors) -> float:
    pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
    expected_goals = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
    factor = team_factors.get(c["team"], 1.0)
    return expected_goals * factor * config.TOPSCORER_MULT[c["position"]]


def fame_score(c, team_factors) -> float:
    """Rival-ownership weight: expected group-phase goals * team factor, WITHOUT the position
    multiplier — models amateurs chasing famous scorers and ignoring that a DEF/GK goal is worth 4x.
    So attackers get over-owned and high-multiplier defenders/keepers under-owned."""
    pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
    expected_goals = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
    return expected_goals * team_factors.get(c["team"], 1.0)


def pick_topscorers(team_factors, n: int = config.TOPSCORER_SLOTS, risk: str = "balanced",
                    candidates=CANDIDATES):
    """Top-n picks. For balanced/aggressive risk, reserve slots for the best
    high-multiplier defenders (a low-ownership, high-ceiling differentiation play
    that pure EV — dominated by elite strikers — would otherwise miss)."""
    scored = sorted(((score_candidate(c, team_factors), c) for c in candidates),
                    key=lambda x: x[0], reverse=True)
    reserve = config.TOPSCORER_DEF_RESERVE.get(risk, 0)
    picks, used = [], set()
    if reserve:
        for ev, c in scored:
            if c["position"] in ("DEF", "GK"):
                picks.append((ev, c, True))
                used.add(c["name"])
                if len(picks) >= reserve:
                    break
    for ev, c in scored:
        if len(picks) >= n:
            break
        if c["name"] not in used:
            picks.append((ev, c, False))
            used.add(c["name"])
    picks.sort(key=lambda x: x[0], reverse=True)
    return [dict(c, ev=round(ev, 3), differentiation=diff) for ev, c, diff in picks[:n]]


def sample_player_goals(candidates, team_factors, sims, rng):
    """Per-world group-stage goals for each candidate ~ Poisson(lambda), with
    lambda = (g90*3*start_prob + PEN_BONUS*pen_share) * team_factor — consistent with the
    topscorer EV model. Returns {name: np.ndarray(sims)}."""
    out = {}
    for c in candidates:
        pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
        exp = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
        lam = max(0.0, exp * team_factors.get(c["team"], 1.0))
        out[c["name"]] = rng.poisson(lam, size=sims)
    return out
