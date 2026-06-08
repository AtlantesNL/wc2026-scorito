"""Expected goals per match: market odds preferred, Elo fallback.

Odds path: Shin de-vig the 1X2 -> ``goal_expectancy`` (Dixon-Coles adjusted) ->
``(home_exp, away_exp)``; if an over/under total line is given, rescale the pair
so their sum equals the line (preserving the supremacy split). Elo path: convert
the rating gap to an expected goal supremacy around the tournament-average total.
"""
from penaltyblog.implied import ImpliedMethod, calculate_implied
from penaltyblog.models import goal_expectancy

from scorito import config

_FLOOR = 0.15  # minimum lambda so the Poisson grid never degenerates


def goals_from_odds(odds, total_line=None):
    """``odds`` = decimal [home, draw, away]. Returns ``(lam_home, lam_away)``."""
    p = calculate_implied(odds, method=ImpliedMethod.SHIN).probabilities
    ge = goal_expectancy(p[0], p[1], p[2], dc_adj=True, rho=config.DC_RHO)
    lam1, lam2 = float(ge["home_exp"]), float(ge["away_exp"])
    if total_line:
        s = lam1 + lam2
        if s > 0:
            lam1 *= total_line / s
            lam2 *= total_line / s
    return max(_FLOOR, lam1), max(_FLOOR, lam2)


def goals_from_elo(elo_home, elo_away, total=config.NEUTRAL_AVG_TOTAL):
    """Neutral-venue expected goals from an Elo gap."""
    sup = (elo_home - elo_away) / config.ELO_GOAL_DIVISOR
    lam1 = max(_FLOOR, (total + sup) / 2.0)
    lam2 = max(_FLOOR, (total - sup) / 2.0)
    return lam1, lam2


def expected_goals(match, odds_map=None, elo=None):
    """Pick the best available signal for one ``Match`` -> ``(lam1, lam2)``.

    ``odds_map``: ``{(team1, team2): {"odds": [h, d, a], "total_line": x|None}}``.
    ``elo``: ``{team_name: rating}``.
    """
    key = (match.team1, match.team2)
    if odds_map and key in odds_map:
        o = odds_map[key]
        return goals_from_odds(o["odds"], o.get("total_line"))
    elo = elo or {}
    return goals_from_elo(elo.get(match.team1, 1500.0), elo.get(match.team2, 1500.0))
