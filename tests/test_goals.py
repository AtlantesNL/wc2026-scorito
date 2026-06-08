from scorito.model.goals import expected_goals, goals_from_elo, goals_from_odds
from scorito.types import Match


def test_goals_from_odds_roundtrip_favorite():
    lam1, lam2 = goals_from_odds(odds=[1.5, 4.0, 6.0])  # strong home favorite
    assert lam1 > lam2 and lam1 > 1.0


def test_goals_from_odds_totals_pins_sum():
    lam1, lam2 = goals_from_odds(odds=[2.0, 3.4, 3.6], total_line=2.5)
    assert abs((lam1 + lam2) - 2.5) < 1e-6


def test_goals_from_elo_monotone_and_floored():
    a1, a2 = goals_from_elo(2000, 1500)  # big gap
    b1, b2 = goals_from_elo(1600, 1500)  # small gap
    assert (a1 - a2) > (b1 - b2)
    assert a2 >= 0.15


def test_expected_goals_prefers_odds_then_elo():
    m = Match(team1="A", team2="B", group="A")
    odds_map = {("A", "B"): {"odds": [1.5, 4.0, 6.0], "total_line": None}}
    lo = expected_goals(m, odds_map=odds_map, elo={"A": 1500, "B": 1500})
    le = expected_goals(m, odds_map={}, elo={"A": 2000, "B": 1500})
    assert lo[0] > lo[1]  # odds path: A favored
    assert le[0] > le[1]  # elo path: A stronger
