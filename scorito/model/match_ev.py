"""Per-match Scorito points for each candidate scoreline.

``ev`` = true expected points: 45·P(exact i-j) + 30·P(correct toto outcome).
``sel`` = the pool-leverage-adjusted *selection* score: the same exact + toto points, each
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
    return config.PTS_EXACT * grid.exact(i, j) + config.PTS_TOTO * toto_weight * p_toto


def _leverage(own: float, n_rivals: int, gamma: float) -> float:
    """Discount for a crowded outcome: 1/(1+own·n_rivals)^gamma (``own`` = rival pick fraction).
    gamma 0, or n_rivals 0, or own 0 -> 1.0 (no discount)."""
    return 1.0 / (1.0 + own * n_rivals) ** gamma


def score_sel(grid, i: int, j: int, own_exact: dict, own_toto: dict,
              n_rivals: int, gamma: float) -> float:
    """Leverage-adjusted selection score: exact + toto points, each discounted by the field's
    ownership of that outcome (so under-owned-but-plausible results — e.g. draws — get boosted)."""
    o = "home" if i > j else "away" if j > i else "draw"
    p_toto = {"home": grid.p_home, "away": grid.p_away, "draw": grid.p_draw}[o]
    ex = config.PTS_EXACT * grid.exact(i, j) * _leverage(own_exact.get((i, j), 0.0), n_rivals, gamma)
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
