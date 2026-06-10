import numpy as np

from scorito.model.grid import ScoreGrid
from scorito.model.match_ev import score_ev, topk_scorelines


def _grid():
    m = np.zeros((3, 3))
    m[1, 0] = 0.4
    m[0, 0] = 0.2
    m[2, 1] = 0.2
    m[1, 1] = 0.1
    m[0, 1] = 0.1
    return ScoreGrid(m, p_home=0.6, p_draw=0.3, p_away=0.1)


def test_score_ev_known_value():
    g = _grid()
    # XOR rule: predict 1-0 -> 30 for the home toto, upgraded to 45 on the exact 1-0 cell.
    # EV = 30*P(home=0.6) + (45-30)*P(exact 1-0 = 0.4) = 18 + 6 = 24  (NOT the additive 36).
    assert abs(score_ev(g, 1, 0) - 24.0) < 1e-9


def test_score_ev_is_xor_not_additive():
    # Locks out the additive double-count bug: Scorito pays max 45/match (an exact hit does
    # not also bank the 30 toto). EV = 30*P(toto) + 15*P(exact), never 45*P(exact) + 30*P(toto).
    g = _grid()
    xor = 30 * g.p_home + (45 - 30) * g.exact(1, 0)        # correct = 24.0
    additive = 45 * g.exact(1, 0) + 30 * g.p_home          # the old bug = 36.0
    assert abs(score_ev(g, 1, 0) - xor) < 1e-9
    assert abs(score_ev(g, 1, 0) - additive) > 1e-6        # must NOT equal the additive value


def test_topk_orders_by_ev():
    g = _grid()
    picks = topk_scorelines(g, k=3)
    assert (picks[0].home, picks[0].away) == (1, 0)
    assert picks[0].ev >= picks[1].ev >= picks[2].ev


def _tilt_grid():
    # home win (1-0) has the broadest toto; the draw (1-1) is the single most
    # likely EXACT score. P(home)=0.50, P(draw)=0.35, P(away)=0.15.
    m = np.zeros((3, 3))
    m[1, 0] = 0.30
    m[2, 0] = 0.20
    m[1, 1] = 0.35
    m[0, 1] = 0.15
    return ScoreGrid(m, p_home=0.50, p_draw=0.35, p_away=0.15)


def test_leverage_tilts_toward_underowned_draw():
    g = _tilt_grid()                                  # 1-0 broad toto; 1-1 modal exact
    safe = topk_scorelines(g, k=1)[0]                 # no field -> raw EV
    assert (safe.home, safe.away) == (1, 0)
    # draw-averse field: the draw outcome is under-owned -> high leverage
    own_exact = {(1, 0): 0.4, (2, 0): 0.3, (1, 1): 0.05, (0, 1): 0.1}
    own_toto = {"home": 0.7, "draw": 0.05, "away": 0.1}
    bold = topk_scorelines(g, k=1, own_exact=own_exact, own_toto=own_toto,
                           n_rivals=30, gamma=0.5)[0]
    assert (bold.home, bold.away) == (1, 1)           # leverage chases the under-owned draw
    assert abs(bold.ev - score_ev(g, 1, 1, 1.0)) < 1e-9   # ev still = true EV
    assert bold.ev != bold.sel
