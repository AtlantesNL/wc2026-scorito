from scorito.eval import datasets


def test_load_intl_filters_tournament_and_builds_history():
    ds = datasets.load_tournament(
        "tests/fixtures/eval/intl_results.csv",
        tournament="FIFA World Cup", years={2018})
    # two WC matches in 2018; the friendly is excluded from the evaluation set
    assert len(ds["eval_matches"]) == 2
    # but the friendly IS used to warm up Elo (history precedes the tournament)
    m = ds["eval_matches"][0]
    assert {"home", "away", "hg", "ag", "home_pre", "away_pre", "neutral"} <= set(m)
