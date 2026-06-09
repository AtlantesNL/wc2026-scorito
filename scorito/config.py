"""Central configuration: scoring constants and model parameters.

Topscorer scoring confirmed from Scorito's in-app "Spelregels" page (group phase):
6 picks; per goal Aanvaller 8 / Middenvelder 16 / Verdediger 32 / Keeper 32, with
each topscorer playing at most 3 group games.
"""

# --- Match scoring (group phase) ---
PTS_EXACT = 45          # exact scoreline correct
PTS_TOTO = 30           # correct outcome (1/X/2) only
PTS_POSITION = 25       # per correctly placed team in the auto-derived group table
MAX_GROUP_POSITION_PTS = 100   # 4 positions x 25

# --- Tournament-level ---
CHAMPION_BONUS = 250    # paid only if your pick lifts the trophy

# Champion P(win): blend weight for the market/Opta prior vs the simulation backbone.
# 0.0 = pure Monte-Carlo, 1.0 = market-anchored.
CHAMPION_MARKET_WEIGHT = 0.5

# --- Topscorers (confirmed from Scorito in-app Spelregels, group phase) ---
# Points per goal by position; each topscorer plays max 3 group games.
# Ratio DEF/GK : MID : ATT = 4 : 2 : 1 is what drives selection.
TOPSCORER_MULT = {"GK": 32, "DEF": 32, "MID": 16, "ATT": 8}
TOPSCORER_SLOTS = 6

# --- Model parameters ---
DC_RHO = 0.001          # Dixon-Coles low-score correction (rho)
MAX_GOALS = 10          # score-grid cutoff (0..MAX_GOALS per team)
TOPK_SCORELINES = 6     # candidate scorelines kept per match for the group enumerator
MC_SIMS = 20000         # Monte-Carlo simulations per group
NEUTRAL_AVG_TOTAL = 2.6 # tournament-average total goals (Elo fallback, neutral venue)
ELO_GOAL_DIVISOR = 250.0  # Elo points per ~1 goal of expected supremacy

# Host advantage (Elo path only; market odds already price it in). Group games for
# the three hosts are effectively home, so we bump their effective rating.
HOSTS = {"USA", "Mexico", "Canada"}
HOST_ELO_BONUS = 100.0  # standard eloratings.net home-advantage value

# Topscorer slots reserved for high-multiplier defenders as differentiation picks.
TOPSCORER_DEF_RESERVE = {"max_ev": 0, "balanced": 2, "aggressive": 3}

# Scoreline risk: how much to down-weight the "toto" points (30, which the whole
# field banks on obvious games) in favour of nailing exact scores (45, the
# differentiator). Boldness scales with pool size — differentiating individual
# scorelines is low-leverage in small pools (variance averages out over 72 games),
# so it only meaningfully kicks in for large pools.
SCORELINE_BOLDNESS = {"max_ev": 0.0, "balanced": 0.3, "aggressive": 0.8}


def scoreline_toto_weight(risk: str, pool_size: int) -> float:
    """Multiplier on the toto term: 1.0 = pure EV, lower = chase exact scores."""
    boldness = SCORELINE_BOLDNESS.get(risk, 0.0)
    pool_factor = max(0.0, min(1.0, (pool_size - 10) / 200.0))
    return 1.0 - min(0.9, boldness * pool_factor)
