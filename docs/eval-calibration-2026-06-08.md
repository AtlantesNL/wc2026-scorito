# Calibration baseline — 8 June 2026

First run of `python -m scorito.eval calibrate` on real historical data: self-computed
Elo warmed over the full martj42 international-results CSV (~49k matches), leave-one-
tournament-out CV across **WC 2014/2018/2022 + Euro 2016/2021/2024** (~345 finals matches).

## Result: the current constants are well-calibrated — no change applied

| Constants | OOS (leave-one-tournament-out) 1X2 log-loss |
|---|---|
| **Current** `DC_RHO=0.001, NEUTRAL_AVG_TOTAL=2.6, ELO_GOAL_DIVISOR=250` | **0.9956** |
| Grid-search optimum (`rho=0.01, total=2.4, divisor=250`) | 1.0076 |
| Uniform-guess baseline (`ln 3`) | 1.0986 |

Per-fold (current constants): WC2014 0.926 · WC2018 0.959 · WC2022 1.077 ·
Euro2016 1.105 · Euro2021 0.934 · Euro2024 1.046.

**Conclusions:**
- The model beats the uniform baseline (1.099) overall and on most tournaments → it
  carries real predictive signal, not noise.
- The grid search does **not** beat the hand-set constants out-of-sample (it overfits the
  training folds, landing at 1.0076 > 0.9956) → **`--write` was NOT applied; constants kept.**
- `ELO_GOAL_DIVISOR=250` was independently chosen by the all-data optimum too → confirmed.
- **Baseline for future model changes: LOTO 1X2 log-loss ≈ 0.996.** Re-run `calibrate`
  after any change and compare against this.

## Reproduce
```bash
mkdir -p data/cache/history && curl -sL \
  https://raw.githubusercontent.com/martj42/international_results/master/results.csv \
  -o data/cache/history/intl_results.csv
.venv/bin/python -m scorito.eval calibrate          # all 6 tournaments, ~12s
```

**Caveats:** Elo here is self-computed (World-Football-Elo style), not eloratings.net; only
the Elo path + the shared `DC_RHO` are exercised historically (free historical odds don't
exist). The live **odds** path is validated separately by `scorecard` during the tournament.
