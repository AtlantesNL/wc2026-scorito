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
    # 1-0: 45*0.4 + 30*P(H=0.6) = 18 + 18 = 36
    assert abs(score_ev(g, 1, 0) - 36.0) < 1e-9


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


def test_toto_weight_tilts_toward_exact_score():
    g = _tilt_grid()
    safe = topk_scorelines(g, k=1, toto_weight=1.0)[0]   # pure EV
    bold = topk_scorelines(g, k=1, toto_weight=0.0)[0]   # ignore the shared toto
    assert (safe.home, safe.away) == (1, 0)              # EV banks the broad home toto
    assert (bold.home, bold.away) == (1, 1)              # bold chases the modal exact score
    # ev always reports TRUE expected points; sel carries the tilt
    assert abs(bold.ev - score_ev(g, 1, 1, 1.0)) < 1e-9
    assert abs(bold.sel - score_ev(g, 1, 1, 0.0)) < 1e-9
    assert bold.ev != bold.sel
