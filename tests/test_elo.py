import json
from pathlib import Path

from scorito.data.elo import (
    get_elo,
    normalize_name,
    parse_teams_tsv,
    parse_world_tsv,
)

FX = Path(__file__).parent / "fixtures"


def test_parse_tsv_samples():
    code2name = parse_teams_tsv((FX / "elo_teams_sample.tsv").read_text(encoding="utf-8"))
    assert code2name["ES"] == "Spain"
    ratings = parse_world_tsv(
        (FX / "elo_world_sample.tsv").read_text(encoding="utf-8"), code2name
    )
    assert ratings["Spain"] == 2155.0
    assert ratings["Czechia"] == 1740.0


def test_normalize_name():
    assert normalize_name("Czech Republic") == "Czechia"
    assert normalize_name("USA") == "United States"
    assert normalize_name("Spain") == "Spain"


def test_get_elo_uses_cache_and_normalizes(tmp_path):
    cache = tmp_path / "elo.json"
    cache.write_text(json.dumps({"Spain": 2155.0, "Czechia": 1740.0}))
    out = get_elo(["Spain", "Czech Republic", "Atlantis"], cache_path=str(cache))
    assert out["Spain"] == 2155.0
    assert out["Czech Republic"] == 1740.0  # via normalization
    assert out["Atlantis"] == 1500.0  # default for unknown
