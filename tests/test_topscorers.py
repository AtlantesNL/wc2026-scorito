from scorito.model.topscorers import pick_topscorers, score_candidate


def test_defender_outranks_attacker_same_expected_goals():
    tf = {"Netherlands": 1.2, "France": 1.2}
    d = dict(name="X", team="Netherlands", position="DEF", g90=0.15, start_prob=0.95, pen_taker=False)
    a = dict(name="Y", team="France", position="ATT", g90=0.15, start_prob=0.95, pen_taker=False)
    assert score_candidate(d, tf) > score_candidate(a, tf)  # 4x multiplier


def test_penalty_taker_bonus_increases_ev():
    tf = {"France": 1.0}
    base = dict(name="X", team="France", position="ATT", g90=0.5, start_prob=0.9, pen_taker=False)
    pen = dict(base, pen_taker=True)
    assert score_candidate(pen, tf) > score_candidate(base, tf)


def test_pick_returns_n_slots_sorted():
    picks = pick_topscorers(team_factors={"Spain": 1.4, "France": 1.3, "Netherlands": 1.1}, n=6)
    assert len(picks) == 6
    evs = [p["ev"] for p in picks]
    assert evs == sorted(evs, reverse=True)


def test_balanced_reserves_more_defenders_than_max_ev():
    tf = {}  # all team factors default to 1.0
    n_def = lambda picks: sum(1 for c in picks if c["position"] in ("DEF", "GK"))
    bal = pick_topscorers(team_factors=tf, n=6, risk="balanced")
    mx = pick_topscorers(team_factors=tf, n=6, risk="max_ev")
    assert n_def(bal) >= 2  # balanced reserves defender differentiation slots
    assert n_def(bal) >= n_def(mx)
