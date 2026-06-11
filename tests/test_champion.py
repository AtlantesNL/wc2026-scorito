from scorito.model.champion import recommend_champion, reorder_for_pool_win

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


# Pool-win MC is a noisy near-tie; it may rank a lower-EV team first. The
# reorder must follow it only in the leverage modes — max_ev keeps EV order.
POOL_WIN = {"France": 0.088, "Argentina": 0.086, "Spain": 0.076}


def test_reorder_leverage_mode_puts_pool_win_argmax_first():
    recs = recommend_champion(PWIN, pool_size=32, risk="balanced")
    out = reorder_for_pool_win(recs, "France", POOL_WIN, "balanced")
    assert out[0].team == "France"
    assert [r.team for r in out[1:3]] == ["Argentina", "Spain"]


def test_reorder_max_ev_keeps_pure_ev_order():
    recs = recommend_champion(PWIN, pool_size=32, risk="max_ev")
    out = reorder_for_pool_win(recs, "France", POOL_WIN, "max_ev")
    assert out[0].team == "Spain"          # highest outright, NOT the pool-win argmax
    assert [r.team for r in out] == [r.team for r in recs]
