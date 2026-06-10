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


def test_sample_player_goals_mean_scales_with_rate_and_factor():
    import numpy as np
    from scorito.model.topscorers import sample_player_goals
    cands = [dict(name="Striker", team="X", position="ATT", g90=0.6, start_prob=1.0, pen_taker=False),
             dict(name="Defender", team="X", position="DEF", g90=0.05, start_prob=1.0, pen_taker=False)]
    rng = np.random.default_rng(0)
    goals = sample_player_goals(cands, {"X": 1.0}, sims=20000, rng=rng)
    # lambda = g90*3*start (+0); striker ~1.8, defender ~0.15 over the 3 group games
    assert 1.6 < goals["Striker"].mean() < 2.0
    assert 0.05 < goals["Defender"].mean() < 0.25
    assert goals["Striker"].shape == (20000,)


def test_fame_score_drops_multiplier():
    from scorito.model.topscorers import fame_score
    tf = {"T": 1.0}
    att = dict(name="A", team="T", position="ATT", g90=0.5, start_prob=1.0)
    dfn = dict(name="D", team="T", position="DEF", g90=0.125, start_prob=1.0)
    # equal expected GOALS*4 vs *1 -> equal Scorito EV, but fame (goals only) is 4x for the attacker
    assert abs(score_candidate(att, tf) - score_candidate(dfn, tf)) < 1e-9
    assert abs(fame_score(att, tf) - 4 * fame_score(dfn, tf)) < 1e-9


def test_build_expected_goals_market_blend_and_backcompat():
    import math
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals, score_candidate, fame_score
    matches = [SimpleNamespace(team1="USA", team2="Paraguay"),
               SimpleNamespace(team1="USA", team2="Uruguay"),
               SimpleNamespace(team1="Wales", team2="USA")]
    tf = {"USA": 1.0}
    cand = dict(name="Christian Pulisic", team="USA", position="ATT", g90=0.47, start_prob=0.9)
    # priced in match 1 only -> blend (market match 1 + hand matches 2,3)
    atgs = {("USA", "Paraguay"): {"christian pulisic": 2.5}}
    out = build_expected_goals([cand], matches, atgs, tf, margin=1.06)[0]
    p = (1 / 2.5) / 1.06
    expected = -math.log(1 - p) + 2 * (0.47 * 0.9 * 1.0)            # 1 market + 2 hand matches
    assert abs(out["exp_goals"] - expected) < 1e-6
    assert out["goals_src"] == "blend"
    assert abs(score_candidate(out, tf) - out["exp_goals"] * 8) < 1e-9   # ATT mult, no team_factor re-applied
    # backward compat: a candidate without exp_goals uses the g90 path unchanged
    assert abs(score_candidate(cand, tf) - (0.47 * 3 * 0.9) * 1.0 * 8) < 1e-9
    assert abs(fame_score(out, tf) - out["exp_goals"]) < 1e-9


def test_build_expected_goals_atgs_plain_name_fallback():
    # Candidate is aliased (Haaland -> "Erling Braut Haaland") but tomorrow's feed lists the
    # PLAIN name -> must still match via the plain-name fallback, not silently use hand g90.
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals
    matches = [SimpleNamespace(team1="Norway", team2="X")]
    cand = dict(name="Erling Haaland", team="Norway", position="ATT", g90=0.8, start_prob=1.0)
    atgs = {("Norway", "X"): {"erling haaland": 1.5}}      # plain name, NOT the alias key
    out = build_expected_goals([cand], matches, atgs, {"Norway": 1.0}, margin=1.06)[0]
    assert out["goals_src"] == "market"                    # found via plain-name fallback


def test_build_expected_goals_market_scaled_by_appearance():
    # A low-start (bench-risk) player's market goal rate is scaled by appearance prob, so a
    # rotation player can't gatecrash the six on an unconditional market rate.
    import math
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals
    matches = [SimpleNamespace(team1="X", team2="Y")]
    cand = dict(name="Benchy", team="X", position="ATT", g90=0.5, start_prob=0.6)
    atgs = {("X", "Y"): {"benchy": 2.5}}
    out = build_expected_goals([cand], matches, atgs, {"X": 1.0}, margin=1.06)[0]
    p = (1 / 2.5) / 1.06
    appear = min(1.0, 0.6 + 0.15)                           # 0.75
    assert abs(out["exp_goals"] - (-math.log(1 - p) * appear)) < 1e-9
    assert out["goals_src"] == "market"


def test_build_expected_goals_opponent_specific_hand_fallback():
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals
    matches = [SimpleNamespace(team1="DE", team2="Minnow"), SimpleNamespace(team1="DE", team2="Tough")]
    cand = dict(name="X", team="DE", position="MID", g90=0.2, start_prob=1.0)
    tf = {"DE": 2.0}                                   # inflated group-average factor
    lams = {("DE", "Minnow"): (3.0, 0.3), ("DE", "Tough"): (1.0, 1.2)}   # DE scores 3 vs Minnow, 1 vs Tough
    out = build_expected_goals([cand], matches, {}, tf, match_lams=lams, avg_lam=1.5)[0]
    expected = 0.2 * 1.0 * (3.0 / 1.5) + 0.2 * 1.0 * (1.0 / 1.5)   # opponent-specific per match
    assert abs(out["exp_goals"] - expected) < 1e-9
    # backward-compat: no match_lams -> group-average team_factor (2.0) for every match
    out2 = build_expected_goals([cand], matches, {}, tf)[0]
    assert abs(out2["exp_goals"] - 2 * (0.2 * 1.0 * 2.0)) < 1e-9
