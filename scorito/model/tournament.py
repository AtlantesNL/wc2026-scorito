"""Full-tournament Monte-Carlo -> P(win) + advancement for all 48 teams.

Group matches are sampled from their (odds/Elo) grids; knockout ties use a precomputed
Elo advance matrix (no KO odds exist). Reuses the group-sim primitives."""
import numpy as np

from scorito import config
from scorito.model.bracket import (GroupPos, LoserOf, ThirdSlot, WinnerOf,
                                    assign_thirds, qualify_thirds)
from scorito.model.goals import goals_from_elo
from scorito.model.grid import build_grid
from scorito.model.group_sim import _award, _rank_table, _sample_scores

ROUND_NEXT = {
    "Round of 32": "r16",
    "Round of 16": "qf",
    "Quarter-final": "sf",
    "Semi-final": "final",
    "Final": "win",
}


def advance_matrix(teams, elo):
    """``{(A, B): P(A wins a KO tie vs B)}`` = p_win + 0.5*p_draw from a neutral Elo grid."""
    P = {}
    for i, a in enumerate(teams):
        for b in teams[i + 1:]:
            l1, l2 = goals_from_elo(elo.get(a, 1500.0), elo.get(b, 1500.0))
            g = build_grid(l1, l2)
            pa = g.p_home + 0.5 * g.p_draw
            P[(a, b)] = pa
            P[(b, a)] = 1.0 - pa
    return P
