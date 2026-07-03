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

# --- Match scoring (knockout phase) ---
# Confirmed from Scorito in-app: "stand na max. 120 minuten" (result incl. extra time; the penalty
# shootout does NOT change the recorded score). XOR like the group phase, doubled: exact pays 90
# (NOT 90+60), correct toto (1/X/2) pays 60. A draw is a valid pick (tie after 120' -> decided on pens).
PTS_KO_EXACT = 90
PTS_KO_TOTO = 60

# Extra-time goal uplift for the recorded 120' score: a match level after 90' plays ~30 more minutes,
# so expected goals scale by (1 + ET_MINUTE_SHARE * P(draw@90')). 30/90 = 1/3. Modest (~+8-9%);
# nudges some modal cells 1-0 -> 2-1 and slightly lowers draw probability. (Aggregate-correct
# approximation; exact ET-convolution would be 2nd-order given the toto term dominates EV.)
ET_MINUTE_SHARE = 1.0 / 3.0

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

# Knockout topscorers (confirmed in-app): pick 4, goals THIS ROUND only (per-round, not cumulative),
# excl. penalty shootout. Multipliers doubled vs group, same 4:2:1 ratio.
KO_TOPSCORER_MULT = {"GK": 64, "DEF": 64, "MID": 32, "ATT": 16}
KO_TOPSCORER_SLOTS = 4
# Single-game penalty bonus (vs the group's PEN_BONUS=0.20 spread over 3 games): ~0.20/3.
KO_PEN_BONUS = 0.07

# Brace de-bias for single-game knockout topscorer EV. Per-goal EV = E[goals]*mult over-credits the
# Poisson tail (2+ goals in one match), which — because a MID's multiplier is 2x an ATT's — spuriously
# lifts high-volume midfielders above strikers. Credit the "goals beyond the first" term ATT-ONLY;
# non-attackers are scored on P(>=1 goal). (None => full per-goal credit = the R32 method.)
KO_BRACE_CREDIT = {"ATT": 1.0, "MID": 0.0, "DEF": 0.0, "GK": 0.0}

# Per-round knockout scoring (confirmed in-app). Each round scales up from the group phase but keeps
# both ratios constant — exact:toto = 3:2 and DEF/GK:MID:ATT = 4:2:1 — so the max_ev pick *shape* is
# identical round to round; only the reported points and the lead-dashboard math change.
#   group 45/30 (8/16/32) -> R32 90/60 (16/32/64) [2x] -> R16 135/90 (24/48/96) [3x]
# form_games = games played entering the round (group 3, then +1 per knockout round), used by the
# realized-form g90 blend. `brace_credit` = the single-game de-bias policy (R32 None => byte-identical
# to the shipped R32 run; R16 credits braces ATT-only). R32 row == the legacy KO_* constants.
KO_ROUND_SCORING = {
    "Round of 32": dict(exact=PTS_KO_EXACT, toto=PTS_KO_TOTO, mult=KO_TOPSCORER_MULT,
                        slots=KO_TOPSCORER_SLOTS, form_games=3, pen_bonus=KO_PEN_BONUS,
                        brace_credit=None),
    "Round of 16": dict(exact=135, toto=90, mult={"GK": 96, "DEF": 96, "MID": 48, "ATT": 24},
                        slots=4, form_games=4, pen_bonus=KO_PEN_BONUS, brace_credit=KO_BRACE_CREDIT),
}
# Realized-form blend (group-stage retrospective: club-g90 alone under-rated in-form scorers like
# Messi and over-rated goal-shy creators like Wirtz). Effective non-pen g90 shrinks the tournament
# rate toward the club prior: (prior_games*club_g90 + tourn_nonpen_goals) / (prior_games + games).
FORM_PRIOR_GAMES = 6

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
