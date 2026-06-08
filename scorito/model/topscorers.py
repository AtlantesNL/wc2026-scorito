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
