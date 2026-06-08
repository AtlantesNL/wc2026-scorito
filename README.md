# Scorito World Cup 2026 — Pick Optimizer

Recommends group-phase Scorito picks: 72 match scorelines (jointly optimized with
the auto-derived group standings), 6 topscorers (exploiting the defender goal
multiplier), and a champion pick. Tuned for a ~30–50 person pool, balanced risk.

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

## Status

v1 = group phase. Re-run per phase as the knockout bracket is revealed.
