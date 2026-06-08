"""Topscorer EV model.

EV = (expected group-phase goals) * team_attack_factor * position_multiplier
where expected goals ~= g90 * 3 games * start_prob (+ a penalty bonus), and the
multiplier (GK/DEF=4, MID=2, ATT=1) is what makes penalty-taking defenders so
valuable. ``team_attack_factor`` (from the goals model) scales by how much the
player's side is expected to score across its three group games.
"""
from scorito import config
from scorito.data.topscorer_candidates import CANDIDATES

PEN_BONUS = 0.20  # extra expected group-phase goals for a first-choice penalty taker


def score_candidate(c, team_factors) -> float:
    expected_goals = c["g90"] * 3 * c["start_prob"] + (PEN_BONUS if c.get("pen_taker") else 0.0)
    factor = team_factors.get(c["team"], 1.0)
    return expected_goals * factor * config.TOPSCORER_MULT[c["position"]]


def pick_topscorers(team_factors, n: int = config.TOPSCORER_SLOTS, candidates=CANDIDATES):
    scored = [(score_candidate(c, team_factors), c) for c in candidates]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(c, ev=round(ev, 3)) for ev, c in scored[:n]]
