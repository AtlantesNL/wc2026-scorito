from scorito.eval import elohist


def test_expected_score_symmetry():
    assert elohist.expected(1500, 1500, ha=0) == 0.5


def test_higher_rated_gains_less_on_win():
    # equal teams, home wins 1-0 (G=1): winner gains K*1*(1-0.5)=20 at K=40
    ratings = {}
    pre = elohist.update(ratings, "A", "B", 1, 0, k=40, ha=0)
    assert pre == (1500.0, 1500.0)
    assert ratings["A"] == 1520.0 and ratings["B"] == 1480.0


def test_goal_diff_multiplier():
    assert elohist.goal_mult(1) == 1.0
    assert elohist.goal_mult(2) == 1.5
    assert elohist.goal_mult(3) == (11 + 3) / 8


def test_run_history_records_prematch_ratings():
    matches = [
        dict(date="2018-01-01", home="A", away="B", hg=1, ag=0, neutral=False),
        dict(date="2018-02-01", home="A", away="C", hg=0, ag=0, neutral=True),
    ]
    pre = elohist.run_history(matches)
    assert pre[0]["home_pre"] == 1500.0 and pre[0]["away_pre"] == 1500.0
    assert pre[1]["home_pre"] > 1500.0  # A won its first game
