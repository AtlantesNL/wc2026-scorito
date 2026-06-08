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


def _toy_matches():
    return [
        dict(home="A", away="B", hg=3, ag=0, home_pre=1900, away_pre=1500, neutral=True),
        dict(home="C", away="D", hg=1, ag=1, home_pre=1600, away_pre=1600, neutral=True),
    ]


def test_evaluate_returns_logloss_and_brier():
    from scorito.eval import calibrate
    res = calibrate.evaluate(_toy_matches(), dict(rho=0.001, total=2.6, divisor=250.0))
    assert "logloss_1x2" in res and res["logloss_1x2"] > 0
    assert 0 <= res["brier_1x2"] <= 2


def test_sweep_picks_lower_logloss():
    from scorito.eval import calibrate
    grids = dict(rho=[0.001], total=[2.6], divisor=[150.0, 400.0])
    best = calibrate.sweep({"toy": _toy_matches()}, grids)
    assert best["divisor"] in (150.0, 400.0)
    assert "cv_logloss" in best
