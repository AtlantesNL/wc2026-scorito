from scorito.eval import results


def test_played_results_parses_ft_scores():
    r = results.played_results("tests/fixtures/eval/wc_played.json")
    assert r[("Mexico", "South Africa")] == (2, 0)
    assert r[("South Korea", "Czech Republic")] == (1, 1)


def test_unplayed_matches_are_skipped(tmp_path):
    p = tmp_path / "f.json"
    p.write_text('{"matches":[{"team1":"A","team2":"B","group":"Group A"}]}')
    assert results.played_results(str(p)) == {}
