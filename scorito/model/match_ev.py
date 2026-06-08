"""Per-match expected Scorito points for each candidate scoreline.

EV(i,j) = 45 * P(exact i-j) + 30 * P(correct toto outcome of i-j).
Returns the top-K scorelines, which the group optimizer then combines.
"""
from scorito import config
from scorito.types import Scoreline


def score_ev(grid, i: int, j: int, toto_weight: float = 1.0) -> float:
    """Expected points for predicting i-j. ``toto_weight`` < 1 down-weights the
    (commoditized) toto term, tilting toward nailing the exact score. The true EV
    is ``toto_weight=1.0``."""
    if i > j:
        p_toto = grid.p_home
    elif j > i:
        p_toto = grid.p_away
    else:
        p_toto = grid.p_draw
    return config.PTS_EXACT * grid.exact(i, j) + config.PTS_TOTO * toto_weight * p_toto


def topk_scorelines(grid, k: int = config.TOPK_SCORELINES, toto_weight: float = 1.0):
    """Top-k scorelines ranked by the (risk-tilted) selection score. Each keeps its
    true EV (``ev``) for reporting and the tilted score (``sel``) for optimization."""
    n = grid.matrix.shape[0]
    cands = [
        Scoreline(i, j, ev=score_ev(grid, i, j, 1.0), sel=score_ev(grid, i, j, toto_weight))
        for i in range(n)
        for j in range(n)
    ]
    cands.sort(key=lambda s: s.sel, reverse=True)
    return cands[:k]
