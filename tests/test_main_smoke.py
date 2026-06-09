from pathlib import Path

from scorito import main
from scorito.data import fixtures

SAMPLE = str(Path(__file__).parent / "fixtures" / "worldcup_sample.json")


def test_elo_only_pipeline_runs(monkeypatch, tmp_path):
    sample_matches = fixtures.load_fixtures(SAMPLE)  # load BEFORE patching to avoid recursion
    monkeypatch.setattr(main.fixtures, "load_fixtures", lambda *a, **k: sample_matches)
    monkeypatch.setattr(main.elo, "get_elo", lambda teams, *a, **k: {t: 1600.0 for t in teams})
    res = main.run(no_odds=True, pool_size=40, risk="balanced", out_dir=str(tmp_path), sims=400)
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "picks.csv").exists()
    assert len(res.groups) == 1  # sample fixture has only Group A
    assert len(res.topscorers) == 6
    assert not res.used_odds
    assert res.advance == {}  # 1-group sample -> champion MC guarded off, falls back to prior
    assert res.pool_win == {}  # 1-group sample -> pool-win guarded off
