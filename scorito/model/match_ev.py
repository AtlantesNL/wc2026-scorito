"""Per-match Scorito points for each candidate scoreline.

Scorito scores a match XOR, not additively: an exact-score hit pays 45, a correct toto (1/X/2)
pays 30, and an exact hit does NOT also collect the toto 30 — max 45 per match (confirmed from
the in-app Spelregels). So the expected points of predicting (i, j) decompose as

    30·P(correct toto outcome)  +  (45−30)·P(exact i-j)

i.e. the exact cell is *upgraded* 30→45, never stacked to 75.

``ev``  = those true expected points.
``sel`` = the pool-leverage-adjusted *selection* score: the same toto + exact-upgrade terms, each
discounted by how crowded that outcome is in the field (the per-match analog of the champion
leverage). The group optimizer ranks/combines on ``sel`` but reports ``ev``.
"""
from scorito import config
from scorito.types import Scoreline


def score_ev(grid, i: int, j: int, toto_weight: float = 1.0) -> float:
    """True EV (``toto_weight=1.0``). ``toto_weight`` is kept only so existing callers/tests can
    still read the pure expected points; selection now goes through ``score_sel``."""
    if i > j:
        p_toto = grid.p_home
    elif j > i:
        p_toto = grid.p_away
    else:
        p_toto = grid.p_draw
    # XOR rule: 30 for the toto class, upgraded to 45 on the exact cell -> only the (45−30)
    # *extra* is attributed to nailing the score (NOT a full 45 on top of the 30).
    return (config.PTS_EXACT - config.PTS_TOTO) * grid.exact(i, j) + config.PTS_TOTO * toto_weight * p_toto


def _leverage(own: float, n_rivals: int, gamma: float) -> float:
    """Discount for a crowded outcome: 1/(1+own·n_rivals)^gamma (``own`` = rival pick fraction).
    gamma 0, or n_rivals 0, or own 0 -> 1.0 (no discount)."""
    return 1.0 / (1.0 + own * n_rivals) ** gamma


def score_sel(grid, i: int, j: int, own_exact: dict, own_toto: dict,
              n_rivals: int, gamma: float) -> float:
    """Leverage-adjusted selection score: the toto points + the exact-score upgrade (45−30), each
    discounted by the field's ownership of that outcome (so under-owned-but-plausible results —
    e.g. draws — get boosted). Mirrors ``score_ev``'s XOR decomposition, not an additive 45+30."""
    o = "home" if i > j else "away" if j > i else "draw"
    p_toto = {"home": grid.p_home, "away": grid.p_away, "draw": grid.p_draw}[o]
    ex = (config.PTS_EXACT - config.PTS_TOTO) * grid.exact(i, j) * _leverage(own_exact.get((i, j), 0.0), n_rivals, gamma)
    to = config.PTS_TOTO * p_toto * _leverage(own_toto.get(o, 0.0), n_rivals, gamma)
    return ex + to


def topk_scorelines(grid, k: int = config.TOPK_SCORELINES, own_exact=None, own_toto=None,
                    n_rivals: int = 0, gamma: float = 0.0):
    """Top-k scorelines ranked by the selection score ``sel``; each keeps its true ``ev`` for
    reporting. With no field (``own_exact`` None, or gamma 0, or n_rivals 0) ``sel == ev`` —
    i.e. pure EV — so callers that pass no ownership get the old behaviour."""
    n = grid.matrix.shape[0]
    use_lev = own_exact is not None and gamma > 0 and n_rivals > 0
    oe, ot = own_exact or {}, own_toto or {}
    cands = []
    for i in range(n):
        for j in range(n):
            ev = score_ev(grid, i, j, 1.0)
            sel = score_sel(grid, i, j, oe, ot, n_rivals, gamma) if use_lev else ev
            cands.append(Scoreline(i, j, ev=ev, sel=sel))
    cands.sort(key=lambda s: s.sel, reverse=True)
    return cands[:k]
