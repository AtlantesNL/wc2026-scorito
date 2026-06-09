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

# Pool-win (field) model.
FIELD_SHARPNESS = 1.5      # field chalkiness exponent (1 = rivals pick ~ true prob; higher = chalkier).
                           # 1.5 = realistic amateur dispersion (chase news-favourites somewhat, disperse
                           # on feelings/home bias) — NOT a syndicate field (2.0+ over-leverages longshots).
POOL_WIN_SIMS = 15000      # tournament "worlds" sampled for the pool-win evaluator

# Pool-aware scorelines: amateur rivals avoid draws — they pick ~DRAW_AVERSION of the draws the
# model implies. SCORELINE_LEVERAGE_GAMMA discounts crowded outcomes (per risk); pool size enters
# via the leverage denominator (own·(N-1)).
# CALIBRATED against the pool-win evaluator (docs/scoreline-calibration-2026-06-09.md): at a ~32-person
# pool, scoreline draw-differentiation is ≈neutral — the EV lost when the match is NOT a draw cancels
# the separation gained when it is. Aggressive draw-picking (gamma>=0.3) actively tanks pool-win, so
# these are tuned LOW: balanced grabs only the 2-3 highest-conviction under-owned draws (a near-free,
# documented-bias hedge); aggressive (0.2 ~ 8 draws) is the empirical peak against a draw-averse field.
DRAW_AVERSION = 0.4
SCORELINE_LEVERAGE_GAMMA = {"max_ev": 0.0, "balanced": 0.1, "aggressive": 0.2}

# Anytime-goalscorer (ATGS) market -> goal rates. Flat de-vig (ATGS has no clean complementary leg);
# eu+uk regions for book consensus (~2 credits/event x 72 group games on The Odds API free tier).
ATGS_MARGIN = 1.06
ATGS_REGIONS = "eu,uk"

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
