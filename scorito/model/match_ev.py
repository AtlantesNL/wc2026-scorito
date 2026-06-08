"""Per-match expected Scorito points for each candidate scoreline.

EV(i,j) = 45 * P(exact i-j) + 30 * P(correct toto outcome of i-j).
Returns the top-K scorelines, which the group optimizer then combines.
"""
from scorito import config
from scorito.types import Scoreline


def score_ev(grid, i: int, j: int) -> float:
    if i > j:
        p_toto = grid.p_home
    elif j > i:
        p_toto = grid.p_away
    else:
        p_toto = grid.p_draw
    return config.PTS_EXACT * grid.exact(i, j) + config.PTS_TOTO * p_toto


def topk_scorelines(grid, k: int = config.TOPK_SCORELINES):
    n = grid.matrix.shape[0]
    cands = [Scoreline(i, j, score_ev(grid, i, j)) for i in range(n) for j in range(n)]
    cands.sort(key=lambda s: s.ev, reverse=True)
    return cands[:k]
