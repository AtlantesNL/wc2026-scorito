# Scorito World Cup 2026 — Pick Optimizer

Recommends Scorito picks for both the group phase and the knockout rounds. **Group phase:** 72 match scorelines (jointly optimized with
the auto-derived group standings), 6 topscorers, and a champion pick chosen to maximize
**P(finishing 1st in your pool)** — a full-tournament Monte-Carlo (all 48 teams, draw-aware), blended
with a **live de-vigged multi-bookmaker title-odds consensus** (54 teams; Opta cross-check;
[finding](docs/reliable-title-prior-2026-06-09.md)), scored against a modelled rival field
(`FIELD_SHARPNESS`) that fades over-owned favourites. Scorelines are pool-leverage-adjusted to lean off outcomes a draw-averse
amateur field over-owns, but calibrated **near-chalk** — the pool-win evaluator finds scoreline
differentiation is ≈neutral at this pool size
([finding](docs/scoreline-calibration-2026-06-09.md)). Topscorers are **engine-selected** for
P(finishing 1st) against a fame-biased field (rivals over-own famous attackers, so under-owned
high-multiplier defenders/keepers separate us) — a small but real edge, safeguarded to never
underperform the EV pick ([finding](docs/topscorer-ownership-calibration-2026-06-09.md)). Their goal
rates can be sourced from live **anytime-goalscorer market odds** (`--atgs`), blended with the hand
`g90` fallback ([finding](docs/atgs-market-goal-rates-2026-06-09.md)). Tuned for a ~30–50 person pool,
balanced risk.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full design.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

# Optional one-time fixtures cache. The optimizer fetches these live when the file is absent,
# but the test suite and the live scorecard (below) read this local path:
mkdir -p data/cache && curl -sL \
  https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json \
  -o data/cache/worldcup2026.json
```

Run the tests with `.venv/bin/python -m pytest -q` (139 passing).

## Usage

```bash
# Elo-only (no API key, runs anywhere):
.venv/bin/python -m scorito.main --no-odds --pool-size 32 --risk balanced

# With market odds (sharper); get a free key at the-odds-api.com. A keyed run caches the live h2h
# snapshot (data/cache/odds_raw.json) and auto-fetches the WC-winner outright for the champion prior
# — replay both offline (no key/credits) with --odds-file / --winner-file:
.venv/bin/python -m scorito.main --odds-key "$ODDS_API_KEY" --pool-size 32 --risk balanced

# Sharpest: also pull anytime-goalscorer odds for market goal rates (caches data/cache/atgs_raw.json;
# replay later with --atgs-file data/cache/atgs_raw.json — no key/credits):
.venv/bin/python -m scorito.main --odds-key "$ODDS_API_KEY" --atgs --pool-size 32 --risk balanced
```

Outputs `out/report.md` (human) and `out/picks.csv` (for fast transcription).

`--risk` sets how hard every pick leans off raw expected value toward pool-leverage (differentiating
from a chalk-picking amateur field): `max_ev` (pure EV — best when your pool pays several places),
`balanced` (default), `aggressive` (most differentiation — best for winner-take-all).

## Knockout phase (Round of 32 onward)

After the group stage, generate knockout picks — per-tie **scoreline + advancer** and **4 topscorers**,
scored with the confirmed per-round knockout rules (result after extra time, the "stand na 120'"). The
round is selected with `--round`; scoring scales up each round but keeps the same ratios (exact:toto
3:2, DEF/GK:MID:ATT 4:2:1), so the `max_ev` pick *shape* is round-invariant:

| Round | exact / toto | ATT / MID / DEF·GK |
|---|---|---|
| `r32` | 90 / 60 | 16 / 32 / 64 |
| `r16` | 135 / 90 | 24 / 48 / 96 |
| `qf` | 180 / 120 | 32 / 64 / 128 |

```bash
.venv/bin/python -m scorito.knockout --round qf --odds-key "$ODDS_API_KEY" --atgs
```

Writes `out/ko_<round>/{report.md,picks.csv}`. Posture is `max_ev` (**protect a lead** — for a leader
this = mirror the field's chalk, no contrarian picks). Single-game topscorer EV uses an **ATT-only
brace de-bias**: non-attackers are credited on P(≥1 goal) rather than raw per-goal EV — a deliberate
chalk-mirroring tilt (the 2026-07-08 empirical review found braces Poisson-consistent at every
position; the real longshot inflation is bookmaker margin, documented in `topscorers.py`). When
leading, the report adds a **lead-protection dashboard** (gap to each rival + swing math). Re-run
per round as the bracket resolves. Round runbooks:
[R32](docs/knockout-r32-handoff-2026-06-28.md) · [R16](docs/knockout-r16-handoff-2026-07-03.md) ·
[QF](docs/knockout-qf-handoff-2026-07-08.md).

## Validation

Measure prediction quality and grade live picks (`scorito/eval/`, free data only):

```bash
# Live scorecard: realized Scorito points for your picks vs baselines (always-1-0 scorelines,
# market top-6 topscorers) as group results arrive. Reads data/cache/worldcup2026.json (the
# openfootball file from Setup — refresh it to pull in live scores); drop data/wc2026_scorers.json
# as {"Player": goals} to enable topscorer grading.
.venv/bin/python -m scorito.eval scorecard

# Calibrate DC_RHO / NEUTRAL_AVG_TOTAL / ELO_GOAL_DIVISOR on past tournaments via a
# self-computed Elo over the martj42 international-results CSV, with honest
# leave-one-tournament-out CV. Add --write to update config.py.
mkdir -p data/cache/history && curl -sL \
  https://raw.githubusercontent.com/martj42/international_results/master/results.csv \
  -o data/cache/history/intl_results.csv          # one-time download
.venv/bin/python -m scorito.eval calibrate --tournaments wc2018,wc2022,euro2024
```

Design: [`docs/superpowers/specs/2026-06-08-validation-harness-design.md`](docs/superpowers/specs/2026-06-08-validation-harness-design.md).

## Status

Group phase, Round of 32, and Round of 16 complete — **1st place entering the quarterfinals**
(R16 banked 633 vs 515 expected: 1 exact + 5 totos + Mbappé/Messi; lead +118 on #2, +259 on #3,
in-app verified). **Quarterfinal engine live** (`--round qf`, scoring confirmed in-app): bracket
Fra-Mar · Esp-Bel · Nor-Eng · Arg-Sui, provisional slate all-1-0/0-1 + Kane/Mbappé/Messi/Haaland.
Lock Thu 2026-07-09 22:00 CEST — re-pull odds + transcribe. Runbook (incl. the R16 retro and the
scoreline/topscorer method reviews): [`docs/knockout-qf-handoff-2026-07-08.md`](docs/knockout-qf-handoff-2026-07-08.md).
