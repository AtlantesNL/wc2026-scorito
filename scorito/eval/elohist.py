"""Self-computed national-team Elo through match history (World-Football-Elo style).

Gives reproducible PRE-MATCH ratings for any historical fixture without scraping
date-stamped ratings. Used only by the calibration backtest."""
DEFAULT_K = 40.0
DEFAULT_HA = 65.0  # home advantage in Elo points (0 at neutral sites / tournaments)


def expected(r_home, r_away, ha=DEFAULT_HA):
    return 1.0 / (10 ** (-(r_home + ha - r_away) / 400.0) + 1.0)


def goal_mult(diff: int) -> float:
    diff = abs(diff)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11 + diff) / 8.0


def update(ratings, home, away, hg, ag, k=DEFAULT_K, ha=DEFAULT_HA):
    """Apply one result in place; return the (home_pre, away_pre) ratings."""
    rh = ratings.get(home, 1500.0)
    ra = ratings.get(away, 1500.0)
    we = expected(rh, ra, ha)
    w = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
    delta = k * goal_mult(hg - ag) * (w - we)
    ratings[home] = rh + delta
    ratings[away] = ra - delta
    return rh, ra


def run_history(matches, k=DEFAULT_K, ha=DEFAULT_HA):
    """``matches`` each ``{date, home, away, hg, ag, neutral}``; returns the same list
    sorted by date and annotated with ``home_pre``/``away_pre`` (ratings BEFORE that
    match)."""
    ratings, out = {}, []
    for m in sorted(matches, key=lambda x: x["date"]):
        h = 0.0 if m.get("neutral") else ha
        rh, ra = update(ratings, m["home"], m["away"], m["hg"], m["ag"], k=k, ha=h)
        out.append(dict(m, home_pre=rh, away_pre=ra))
    return out
