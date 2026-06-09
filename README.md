# Scorito World Cup 2026 — Pick Optimizer

Recommends group-phase Scorito picks: 72 match scorelines (jointly optimized with
the auto-derived group standings), 6 topscorers, and a champion pick (chosen from a
full-tournament Monte-Carlo of all 48 teams — draw-aware, blended with market title
odds via `CHAMPION_MARKET_WEIGHT`). Tuned for a ~30–50 person pool, balanced risk.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full design.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

## Usage

```bash
# Elo-only (no API key, runs anywhere):
.venv/bin/python -m scorito.main --no-odds --pool-size 40 --risk balanced

# With market odds (sharper); get a free key at the-odds-api.com:
.venv/bin/python -m scorito.main --odds-key "$ODDS_API_KEY" --pool-size 40 --risk balanced
```

Outputs `out/report.md` (human) and `out/picks.csv` (for fast transcription).

## Validation

Measure prediction quality and grade live picks (`scorito/eval/`, free data only):

```bash
# Live scorecard: realized Scorito points for your picks vs baselines (always-1-0,
# chalk champion, market top-6) as group results arrive. Auto-reads the openfootball
# feed; drop data/wc2026_scorers.json as {"Player": goals} to enable topscorer grading.
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

v1 = group phase. Re-run per phase as the knockout bracket is revealed.
