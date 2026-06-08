import pytest

from scorito.model.grid import build_grid


@pytest.fixture
def asymmetric_group():
    """A 4-team group with A strongest, C/D weak — used by the optimizer tests."""
    teams = ["A", "B", "C", "D"]
    matches = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]
    lam = {
        ("A", "B"): (1.8, 0.8),
        ("A", "C"): (2.0, 0.7),
        ("A", "D"): (2.2, 0.5),
        ("B", "C"): (1.4, 1.1),
        ("B", "D"): (1.6, 0.9),
        ("C", "D"): (1.3, 1.0),
    }
    grids = {m: build_grid(*lam[m]) for m in matches}
    return teams, matches, grids
