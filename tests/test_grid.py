from scorito.model.grid import ScoreGrid, build_grid


def test_grid_sums_to_one_and_1x2_consistent():
    g = build_grid(1.6, 0.9)
    assert abs(g.matrix.sum() - 1.0) < 1e-6
    assert abs((g.p_home + g.p_draw + g.p_away) - 1.0) < 1e-9
    assert g.p_home > g.p_away  # higher home lambda


def test_exact_matches_matrix():
    g = build_grid(1.6, 0.9)
    assert abs(g.exact(1, 0) - g.matrix[1, 0]) < 1e-12


def test_score_grid_interface_construct():
    import numpy as np

    m = np.zeros((2, 2))
    m[1, 0] = 1.0
    g = ScoreGrid(m, p_home=1.0, p_draw=0.0, p_away=0.0)
    assert g.exact(1, 0) == 1.0
