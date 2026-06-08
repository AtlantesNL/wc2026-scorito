from scorito.model.champion import ChampionRec
from scorito.model.group_opt import GroupResult
from scorito.report import build_csv_rows
from scorito.types import Scoreline


def _group_result():
    matches = [("M", "S"), ("M", "K"), ("M", "C"), ("S", "K"), ("S", "C"), ("K", "C")]
    scorelines = [Scoreline(1, 0, 10.0) for _ in range(6)]
    return GroupResult(
        group="A", teams=["M", "S", "K", "C"], matches=matches, scorelines=scorelines,
        predicted_standing=["M", "S", "K", "C"], match_pts=60, stand_pts=50,
        total=110, naive_total=110,
    )


def test_csv_has_row_per_match_plus_meta():
    champion = [
        ChampionRec("France", 0.15, 37.5, 0.23, 0.05),
        ChampionRec("Spain", 0.16, 40.0, 0.25, 0.048),
    ]
    topscorers = [dict(name="Mbappe", team="France", position="ATT", pen_taker=True, ev=3.2)]
    rows = build_csv_rows({"A": _group_result()}, champion=champion, topscorers=topscorers)
    assert sum(1 for r in rows if r["type"] == "match") == 6
    assert sum(1 for r in rows if r["type"] == "standing") == 4
    assert any(r["type"] == "champion" for r in rows)
    assert any(r["type"] == "topscorer" for r in rows)
