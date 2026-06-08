"""Central configuration: scoring constants and model parameters.

Two scoring values are contested across public sources and must be confirmed on
Scorito's in-app "Spelregels" page before locking picks (see docs/DESIGN.md §1):
the absolute topscorer per-goal base (8/16/32 vs 16/32/64) and the group-phase
topscorer slot count (4 vs 6). The DEF:MID:ATT = 4:2:1 *ratio* is robust either
way, and only the ratio affects topscorer selection.
"""

# --- Match scoring (group phase) ---
PTS_EXACT = 45          # exact scoreline correct
PTS_TOTO = 30           # correct outcome (1/X/2) only
PTS_POSITION = 25       # per correctly placed team in the auto-derived group table
MAX_GROUP_POSITION_PTS = 100   # 4 positions x 25

# --- Tournament-level ---
CHAMPION_BONUS = 250    # paid only if your pick lifts the trophy

# --- Topscorers ---
# Relative per-goal multiplier by position (absolute base contested - confirm in-app).
TOPSCORER_MULT = {"GK": 4, "DEF": 4, "MID": 2, "ATT": 1}
TOPSCORER_SLOTS = 6     # group phase (blog says 4 - confirm in-app)

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
