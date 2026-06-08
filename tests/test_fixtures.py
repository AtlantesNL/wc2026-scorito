from pathlib import Path

from scorito.data.fixtures import load_fixtures, group_teams

SAMPLE = Path(__file__).parent / "fixtures" / "worldcup_sample.json"


def test_load_groups_and_matches():
    matches = load_fixtures(str(SAMPLE))
    g = [m for m in matches if m.group == "A"]
    assert len(g) == 6
    assert all(m.team1 and m.team2 for m in g)
    assert all(m.group == "A" for m in g)


def test_group_teams_four_unique():
    teams = group_teams(load_fixtures(str(SAMPLE)))["A"]
    assert len(teams) == 4 and len(set(teams)) == 4
    assert "Czech Republic" in teams


def test_knockout_matches_excluded():
    matches = load_fixtures(str(SAMPLE))
    assert all(m.group for m in matches)
