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
