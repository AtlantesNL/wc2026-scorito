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

# Prediction-market title probabilities where the research gave explicit figures.
MARKET = {
    "France": 0.17,
    "Spain": 0.16,
}


def blended_probs() -> dict[str, float]:
    """Genuine title probabilities: average Opta+market where both exist."""
    out = {}
    for team, p in OPTA.items():
        out[team] = 0.5 * p + 0.5 * MARKET[team] if team in MARKET else p
    return out
