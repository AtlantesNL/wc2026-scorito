from scorito.model.champion import recommend_champion

# A fixed P(win) dict so these tests exercise only the leverage layer.
PWIN = {"Spain": 0.18, "France": 0.15, "Brazil": 0.12, "England": 0.10,
        "Argentina": 0.09, "Germany": 0.06, "Netherlands": 0.05}


def test_ev_points_is_p_times_bonus():
    recs = {r.team: r for r in recommend_champion(PWIN, pool_size=40, risk="balanced")}
    assert abs(recs["Spain"].ev_points - PWIN["Spain"] * 250) < 1e-9


def test_larger_pool_pushes_off_the_consensus_favorite():
    def rank_of(recs, team):
        return [r.team for r in recs].index(team)
    small = recommend_champion(PWIN, pool_size=8, risk="balanced")
    large = recommend_champion(PWIN, pool_size=400, risk="balanced")
    assert rank_of(large, "Spain") >= rank_of(small, "Spain")


def test_max_ev_ranks_by_pure_win_prob():
    recs = recommend_champion(PWIN, pool_size=100, risk="max_ev")
    pwins = [r.p_win for r in recs]
    assert pwins == sorted(pwins, reverse=True)
