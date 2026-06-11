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


def test_fetch_forces_utf8_not_latin1(tmp_path, monkeypatch):
    """Regression: eloratings omits the charset header; requests would default
    to ISO-8859-1 and mojibake 'Curaçao' -> 'CuraÃ§ao' (then defaulted to 1500)."""
    from scorito.data import elo

    teams = "CW\tCuraçao\nES\tSpain\n".encode("utf-8")
    world = "x\ty\tCW\t1434\tz\nx\ty\tES\t2155\tz\n".encode("utf-8")

    class FakeResp:
        def __init__(self, raw):
            self._raw = raw
            self.encoding = "ISO-8859-1"  # what requests picks for charset-less text/*

        @property
        def text(self):
            return self._raw.decode(self.encoding)

    monkeypatch.setattr(elo.requests, "get",
                        lambda url, *a, **k: FakeResp(teams if "teams" in url else world))
    out = get_elo(["Curaçao", "Spain"], cache_path=str(tmp_path / "e.json"), refresh=True)
    assert out["Curaçao"] == 1434.0   # 1500 (defaulted) if decoded as latin-1
    assert out["Spain"] == 2155.0


def test_get_elo_uses_cache_and_normalizes(tmp_path):
    cache = tmp_path / "elo.json"
    cache.write_text(json.dumps({"Spain": 2155.0, "Czechia": 1740.0}))
    out = get_elo(["Spain", "Czech Republic", "Atlantis"], cache_path=str(cache))
    assert out["Spain"] == 2155.0
    assert out["Czech Republic"] == 1740.0  # via normalization
    assert out["Atlantis"] == 1500.0  # default for unknown
