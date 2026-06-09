"""Pre-tournament title probabilities.

Opta supercomputer (theanalyst.com, 25,000 sims, "as of 4 June 2026") plus the
explicit prediction-market numbers the research gave (Polymarket/Kalshi have
France ahead of Spain). Opta is partly odds-derived, so we don't treat the two
as fully independent — we average where both exist (the research's recommended
"robust prior"), otherwise use Opta. Values are genuine probabilities and are NOT
renormalized: the ~25% mass on the other 37 teams is intentionally left implicit.
"""

# Opta title probabilities (top contenders + hosts)
OPTA = {
    "Spain": 0.161,
    "France": 0.130,
    "England": 0.112,
    "Argentina": 0.104,
    "Portugal": 0.070,
    "Brazil": 0.066,
    "Germany": 0.051,
    "Netherlands": 0.036,
    "USA": 0.0121,
    "Mexico": 0.0099,
    "Canada": 0.0052,
}

# Prediction-market title probabilities (Polymarket, ~June 2026). Spain/France co-favourites; Argentina
# and Brazil trail the European favourites. Averaged with Opta in blended_probs (NOT renormalized).
MARKET = {
    "Spain": 0.16,
    "France": 0.16,
    "England": 0.11,
    "Argentina": 0.08,
    "Brazil": 0.08,
}


def blended_probs() -> dict[str, float]:
    """Genuine title probabilities: average Opta+market where both exist."""
    out = {}
    for team, p in OPTA.items():
        out[team] = 0.5 * p + 0.5 * MARKET[team] if team in MARKET else p
    return out


def blend_champion_probs(mc, market, weight=None):
    """Blend the simulation's P(win) (``mc``, all teams, the backbone) with the market/Opta
    prior (``market``, a few teams). The market is extended to all teams by spreading its
    residual mass over the uncovered teams in proportion to ``mc``; then
    ``out = weight*market_full + (1-weight)*mc`` (sums to 1)."""
    from scorito import config
    w = config.CHAMPION_MARKET_WEIGHT if weight is None else weight
    covered = {t: market[t] for t in market if t in mc}
    s = sum(covered.values())
    market_full = dict(covered)
    uncovered = [t for t in mc if t not in covered]
    if s >= 1.0:
        market_full = {t: p / s for t, p in covered.items()}
        for t in uncovered:
            market_full[t] = 0.0
    else:
        denom = sum(mc[t] for t in uncovered) or 1.0
        for t in uncovered:
            market_full[t] = (1.0 - s) * mc[t] / denom
    return {t: w * market_full.get(t, 0.0) + (1.0 - w) * mc[t] for t in mc}
