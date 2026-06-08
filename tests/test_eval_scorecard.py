from scorito.eval import results


def test_played_results_parses_ft_scores():
    r = results.played_results("tests/fixtures/eval/wc_played.json")
    assert r[("Mexico", "South Africa")] == (2, 0)
    assert r[("South Korea", "Czech Republic")] == (1, 1)


def test_unplayed_matches_are_skipped(tmp_path):
    p = tmp_path / "f.json"
    p.write_text('{"matches":[{"team1":"A","team2":"B","group":"Group A"}]}')
    assert results.played_results(str(p)) == {}


def test_parse_picks_csv():
    from scorito.eval import picks as picks_mod
    p = picks_mod.load_picks("tests/fixtures/eval/picks.csv")
    assert p["scorelines"][("Mexico", "South Africa")] == (1, 0)
    assert p["standings"]["A"] == ["Mexico", "South Korea", "Czech Republic", "South Africa"]
    assert p["champion"] == "Spain"
    assert p["topscorers"] == [dict(name="Harry Kane", team="England", position="ATT")]


def test_scorecard_scores_played_matches_and_baseline():
    from scorito.eval import scorecard
    our = {("Mexico", "South Africa"): (1, 0),
           ("South Korea", "Czech Republic"): (2, 0)}
    actual = {("Mexico", "South Africa"): (2, 0),          # our 1-0 -> toto 30
              ("South Korea", "Czech Republic"): (1, 1)}    # our 2-0 -> miss 0
    sc = scorecard.score_scorelines(our, actual)
    assert sc["ours"] == 30
    # always-1-0 baseline: MEX 1-0 vs 2-0 -> 30 ; KOR 1-0 vs 1-1 -> 0
    assert sc["baseline_1_0"] == 30


def test_scorecard_topscorers_vs_market():
    from scorito.eval import scorecard
    ours = [dict(name="Achraf Hakimi", team="Morocco", position="DEF")]
    goals = {"Achraf Hakimi": 1, "Harry Kane": 2}
    sc = scorecard.score_topscorers(ours, goals)
    assert sc["ours"] == 1 * 32          # DEF goal
    assert sc["baseline_market"] == 2 * 8  # Kane (ATT) in MARKET_TOP6
