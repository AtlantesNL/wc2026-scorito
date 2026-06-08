# Validation harness for the Scorito WC2026 optimizer — design spec

**Date:** 2026-06-08 · **Status:** approved (approach **B — measure + calibrate**) · **Author:** R. van Bruggen + Claude

## 1. Problem

Every dial in the model is hand-set with no objective validation — `PEN_BONUS=0.20`,
`NEUTRAL_AVG_TOTAL=2.6`, `ELO_GOAL_DIVISOR=250`, `DC_RHO=0.001`, `est_shares` temp, the
risk tilts. There is no way to tell whether a change improves predictions. This harness
makes prediction quality **measurable** (so tuning stops being guesswork) and turns the
running tournament into a **scorecard** against baselines.

## 2. Goals

- Measure probabilistic accuracy (log-loss, Brier, reliability) of the
  `goals → grid → outcome` model on past tournaments.
- **Calibrate** `DC_RHO`, `NEUTRAL_AVG_TOTAL`, `ELO_GOAL_DIVISOR` to an *out-of-sample*
  optimum (leave-one-tournament-out CV); propose config updates (write only on `--write`).
- **Live scorecard:** realized Scorito points for our picks vs. baselines, per component,
  computed incrementally as WC 2026 results arrive.
- Free data only; all tests network-free (fixtures).

## 3. Non-goals (YAGNI)

- **No historical odds** (unavailable for free) → historical calibration runs the **Elo
  path**; the odds path you use live shares only `DC_RHO` (which transfers) and is otherwise
  validated by the live scorecard.
- No tuning of `est_shares` temp / `GAMMA` (those need pool-entry data, not match history).
- No full historical pick-backtest (that was approach C).
- No auto-write of `config.py` without an explicit `--write` flag.

## 4. Architecture

New isolated package; the existing model is untouched except for optional calibrated
constants written back to `config.py`.

```
scorito/eval/
  __init__.py
  datasets.py    # load historical tournaments (results + Elo) and live WC2026 results
  metrics.py     # pure: log-loss, Brier, reliability bins, realized-Scorito-points helpers
  calibrate.py   # historical replay + constant sweep + leave-one-tournament-out CV
  scorecard.py   # live grader: our picks vs baselines, per component, incremental
  __main__.py    # CLI: `python -m scorito.eval calibrate|scorecard`
tests/
  test_eval_metrics.py
  test_eval_calibrate.py
  test_eval_scorecard.py
```

Each unit is pure logic behind a small IO seam in `datasets.py`. Tests use embedded
fixtures, never the network.

## 5. Data sources (all free)

| Purpose | Source | Cache |
|---|---|---|
| Historical results | openfootball JSON (WC 2014/2018/2022; Euro 2016/2020-21/2024) | `data/cache/history/<tourney>.json` |
| Historical Elo | eloratings.net ratings at each tournament's start date | `data/cache/history/elo_<tourney>.tsv` |
| Live WC2026 results | existing openfootball `worldcup2026` feed (scores fill in as played) | `data/cache/worldcup2026.json` (refreshed) |
| Live goalscorers (optional) | hand-maintained `data/wc2026_scorers.json` `{player: group_goals}` | — |

**Elo approximation:** pre-match ratings are taken as each team's rating at the
tournament's start date (ratings drift slightly within a tournament). Documented; a
per-match refinement is a possible later improvement, not in scope.

## 6. `metrics.py` (the trust anchor — pure functions)

- `log_loss(probs, outcome_idx)`, `brier(probs, outcome_idx)` — categorical (1X2) and binary (O/U 2.5).
- `exact_score_logloss(grid, i, j)` — from `grid.exact(i, j)`, clamped to avoid `log(0)`.
- `reliability_bins(pred, obs, nbins=10)` — predicted-prob vs observed-frequency table.
- Realized Scorito points (reuse `config` constants):
  - `match_points(pick, actual)` → 45 exact / 30 toto / 0.
  - `standings_points(predicted_table, actual_table)` → 25 × correctly-placed teams.
  - `topscorer_points(picks, scorer_goals)` → Σ goals × position multiplier (8/16/32/32).
- Hand-computed unit tests for every function.

## 7. `calibrate.py`

- `replay(dataset, constants)` → predicted 1X2 / exact / O/U per match (Elo path).
- `evaluate(predictions, actuals)` → metrics dict (log-loss, Brier, exact log-loss, reliability).
- `sweep(dataset, grids)` over bounded ranges of `(DC_RHO, NEUTRAL_AVG_TOTAL,
  ELO_GOAL_DIVISOR)`; selects the minimum **mean out-of-sample 1X2 log-loss** under
  **leave-one-tournament-out CV**; also reports Brier / exact / O/U at the optimum.
- Report: current vs. best constants, in-sample and held-out deltas, reliability table.
- `--write` updates `config.py` in place (clear diff; values only, not structure).

## 8. `scorecard.py`

- Inputs: our committed picks (`out/picks.csv`, or re-run the model) + actual results.
- Per-component realized points, **played matches / completed groups only** (incremental):
  scorelines, standings, topscorers (if scorer file present), champion (resolved at end).
- **Baselines** (each scored on its relevant components, incl. the standings its scorelines
  imply): **always-`1-0`** scorelines · **chalk champion** (argmax `P(win)`) ·
  **market-top-6 topscorers** = the six shortest Golden-Boot-odds players that are in a
  confirmed squad, kept as a small constant list in the eval module (sourced from the
  June-2026 odds in `docs/topscorer-research-2026-06-08.md`). Report our points vs. each
  baseline + running totals by matchday.
- Topscorer grading activates iff `data/wc2026_scorers.json` exists (graceful degradation).

## 9. CLI

```
python -m scorito.eval calibrate [--tournaments wc2018,euro2024,...] [--write]
python -m scorito.eval scorecard [--results <feed>] [--scorers data/wc2026_scorers.json] [--picks out/picks.csv]
```

## 10. Error handling

- Missing historical Elo for a team → default 1500 + coverage warning (matches model behaviour).
- Unplayed / incomplete matches → skipped; scorecard is incremental.
- Missing scorers file → topscorer scorecard disabled with a one-line notice.
- Sweep ranges bounded; config never written without `--write`.

## 11. Testing (TDD, network-free)

- `test_eval_metrics`: hand cases for log-loss / Brier / reliability and the three
  realized-points helpers (exact, toto, standings, topscorer).
- `test_eval_calibrate`: a synthetic tournament with a known optimum → `sweep` recovers it;
  leave-one-tournament-out split correctness; Elo-coverage handling.
- `test_eval_scorecard`: fixed picks + fixed results → realized points and baseline deltas
  match hand-computed values; partial (mid-tournament) results handled.

## 12. Risks / honest limitations

- Historical sample is small (~6 tournaments, ~350 matches) → tuning is modest; LOTO CV
  guards overfitting and the report states the out-of-sample confidence.
- Calibration transfers to the live **odds path only via `DC_RHO`**; the two Elo constants
  matter only for matches with no odds.
- Elo-snapshot approximation (§5) introduces minor noise into historical predictions.

## 13. Deliverables

`scorito/eval/{__init__,datasets,metrics,calibrate,scorecard,__main__}.py` +
`tests/test_eval_{metrics,calibrate,scorecard}.py`, with a short `README`/`DESIGN.md`
pointer. No changes to the prediction model beyond optional `config.py` constant updates.
