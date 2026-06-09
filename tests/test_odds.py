import json
from pathlib import Path

from scorito.data.odds import parse_odds

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "odds_sample.json").read_text())


def test_parse_odds_median_and_total():
    m = parse_odds(SAMPLE)
    e = m[("Mexico", "South Africa")]
    assert len(e["odds"]) == 3
    assert abs(e["odds"][0] - 1.85) < 1e-9  # median(1.80, 1.90)
    assert abs(e["odds"][1] - 3.55) < 1e-9  # median(3.60, 3.50)
    assert e["total_line"] == 2.5


def test_parse_odds_name_mapping_and_missing_totals():
    m = parse_odds(SAMPLE)
    assert ("USA", "Paraguay") in m         # "United States" -> "USA"
    assert m[("USA", "Paraguay")]["total_line"] is None  # no totals market in feed


def test_norm_strips_accents_and_case():
    from scorito.data.odds import _norm
    assert _norm("Kylian Mbappé") == "kylian mbappe"
    assert _norm("João  Félix!") == "joao felix"


def test_parse_atgs_median_across_books_and_name_field():
    from scorito.data.odds import parse_atgs
    raw = [{
        "home_team": "United States", "away_team": "Paraguay",
        "bookmakers": [
            {"key": "b1", "markets": [{"key": "player_goal_scorer_anytime", "outcomes": [
                {"name": "Christian Pulisic", "price": 2.0},
                {"name": "Yes", "description": "Folarin Balogun", "price": 3.0}]}]},
            {"key": "b2", "markets": [{"key": "player_goal_scorer_anytime", "outcomes": [
                {"name": "Christian Pulisic", "price": 2.4},
                {"name": "No", "description": "Folarin Balogun", "price": 1.4}]}]},
        ],
    }]
    m = parse_atgs(raw)
    sel = m[("USA", "Paraguay")]
    assert abs(sel["christian pulisic"] - 2.2) < 1e-9     # median(2.0, 2.4)
    assert sel["folarin balogun"] == 3.0                   # "Yes" leg via description; "No" skipped
