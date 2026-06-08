from scorito.model.champion import recommend_champion


def test_ev_points_is_p_times_bonus():
    recs = {r.team: r for r in recommend_champion(pool_size=40, risk="balanced")}
    assert abs(recs["Spain"].ev_points - recs["Spain"].p_win * 250) < 1e-9


def test_larger_pool_pushes_off_the_consensus_favorite():
    def rank_of(recs, team):
        return [r.team for r in recs].index(team)

    small = recommend_champion(pool_size=8, risk="balanced")
    large = recommend_champion(pool_size=400, risk="balanced")
    # Spain is the most over-owned favourite -> it can only rank worse (or equal)
    # as the pool grows, never better.
    assert rank_of(large, "Spain") >= rank_of(small, "Spain")


def test_max_ev_ranks_by_pure_win_prob():
    recs = recommend_champion(pool_size=100, risk="max_ev")
    # with no fade, the ordering is exactly by p_win
    pwins = [r.p_win for r in recs]
    assert pwins == sorted(pwins, reverse=True)
