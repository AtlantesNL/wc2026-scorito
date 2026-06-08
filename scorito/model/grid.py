"""Score-probability grid via penaltyblog's Dixon-Coles adjusted Poisson.

Thin wrapper exposing a stable ``ScoreGrid`` interface so the rest of the code
never touches penaltyblog directly (and a numpy fallback could slot in later).
The 1X2 probabilities are derived from the normalized score matrix itself, so
``p_home + p_draw + p_away == 1`` exactly and stays consistent with ``exact()``.
"""
import numpy as np
from penaltyblog.models import create_dixon_coles_grid

from scorito import config


class ScoreGrid:
    def __init__(self, matrix, p_home, p_draw, p_away):
        self.matrix = matrix
        self.p_home = p_home
        self.p_draw = p_draw
        self.p_away = p_away

    def exact(self, i: int, j: int) -> float:
        return float(self.matrix[i, j])


def build_grid(lam_home, lam_away, rho=config.DC_RHO, max_goals=config.MAX_GOALS) -> ScoreGrid:
    g = create_dixon_coles_grid(lam_home, lam_away, rho=rho, max_goals=max_goals)
    n = max_goals + 1
    m = np.array([[g.exact_score(i, j) for j in range(n)] for i in range(n)], dtype=float)
    m /= m.sum()
    p_home = float(np.tril(m, -1).sum())  # i > j
    p_away = float(np.triu(m, 1).sum())   # j > i
    p_draw = float(np.trace(m))           # i == j
    return ScoreGrid(m, p_home, p_draw, p_away)
