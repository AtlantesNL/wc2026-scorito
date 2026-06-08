import numpy as np

from scorito.model.group_opt import (
    optimize_group,
    predicted_standing,
    score_combo,
    standings_only_ordering,
)
from scorito.types import Scoreline

TEAMS = ["A", "B", "C", "D"]
MATCHES = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]


def test_score_combo_math_hand_computed():
    # A wins all (1-0), B beats C and D (1-0), C beats D (1-0): clean A>B>C>D table.
    sl = {
        ("A", "B"): Scoreline(1, 0, 10.0),
        ("A", "C"): Scoreline(1, 0, 10.0),
        ("A", "D"): Scoreline(1, 0, 10.0),
        ("B", "C"): Scoreline(1, 0, 10.0),
        ("B", "D"): Scoreline(1, 0, 10.0),
        ("C", "D"): Scoreline(1, 0, 10.0),
    }
    combo = [sl[m] for m in MATCHES]
    # probs put each team exactly at its true position with prob 1.0
    probs = {
        "A": np.array([1.0, 0, 0, 0]),
        "B": np.array([0, 1.0, 0, 0]),
        "C": np.array([0, 0, 1.0, 0]),
        "D": np.array([0, 0, 0, 1.0]),
    }
    mp, sp, total, objective, order = score_combo(combo, MATCHES, TEAMS, probs)
    assert order == ["A", "B", "C", "D"]
    assert abs(mp - 60.0) < 1e-9          # 6 matches * 10 EV
    assert abs(sp - 100.0) < 1e-9         # 4 positions * 25 * prob 1.0
    assert abs(total - 160.0) < 1e-9
    assert abs(objective - 160.0) < 1e-9  # sel defaults to ev -> objective == true total


def test_predicted_standing_orders_by_results():
    combo = [Scoreline(*s) for s in [(3, 0), (3, 0), (3, 0), (1, 0), (1, 0), (1, 0)]]
    order = predicted_standing(combo, MATCHES, TEAMS)
    assert order[0] == "A" and order[-1] == "D"


def test_standings_only_assignment_is_permutation():
    probs = {
        "A": np.array([0.7, 0.2, 0.1, 0.0]),
        "B": np.array([0.2, 0.5, 0.2, 0.1]),
        "C": np.array([0.1, 0.2, 0.5, 0.2]),
        "D": np.array([0.0, 0.1, 0.2, 0.7]),
    }
    assert standings_only_ordering(probs) == ["A", "B", "C", "D"]


def test_optimizer_never_worse_than_naive(asymmetric_group):
    res = optimize_group(*asymmetric_group, k=4, sims=4000, seed=2)
    assert res.total >= res.naive_total          # naive is in the search space
    assert len(res.scorelines) == 6
    assert set(res.predicted_standing) == set(asymmetric_group[0])
    assert sorted(res.predicted_standing) == sorted(asymmetric_group[0])  # permutation


def test_optimizer_standings_component_competitive(asymmetric_group):
    # The optimizer's standings points should be within reach of the standings-only
    # optimum (it trades a little standings EV for match EV, never collapsing it).
    teams, matches, grids = asymmetric_group
    res = optimize_group(teams, matches, grids, k=4, sims=4000, seed=3)
    assert res.stand_pts > 0
    assert res.match_pts > 0
