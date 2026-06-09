# Pool-aware scorelines — design spec (Approach A)

**Date:** 2026-06-09 · **Status:** approved (A — per-match ownership-adjusted EV) · **Author:** R. van Bruggen + Claude

## 1. Problem

Scorelines + standings are ~90% of Scorito's points, but the optimizer picks **per-match EV-max**
scorelines → 60/72 are 1-0/0-1, identical to every market-using rival, and the `scoreline_toto_weight`
"boldness" knob is inert at realistic pool sizes (~0.97 at 32). The biggest *exploitable* amateur bias —
**draw-aversion** (real WC group-draw rate ~22%; amateurs predict ~10-15%, so 1-1/0-0 are under-owned
*correct* results) — is unused. Make scoreline selection **pool-aware** so it surgically predicts
under-owned-but-plausible results (especially draws) while staying near-chalk overall.

## 2. Goals / Non-goals

- Replace the raw-EV scoreline *selection* objective (and retire `toto_weight`/`SCORELINE_BOLDNESS`) with a
  **pool-leverage-adjusted** objective driven by a **draw-averse field model**.
- Stay near-chalk for a ~32-person weak pool (lean-chalk + surgical differentiation), with leverage that
  automatically softens as pool size shrinks.
- **Validate** the result with the existing pool-win evaluator (`pool.py`): confirm the new entry raises
  P(finishing 1st) vs the all-chalk entry — evidence, not assertion.
- **Non-goals (YAGNI):** standings-ownership leverage and topscorer-ownership are out of scope (the
  scoreline draws are the big, evidenced lever; the rest is second-order). No nested per-match simulation
  (that was Approach B); this stays per-match + fast.

## 3. Field scoreline-ownership model (the one bias: draw-aversion)

New `field.scoreline_ownership(grid, draw_aversion, sharpness)` → `(own_exact, own_toto)`:
- `w(i,j) = grid.exact(i,j) * (draw_aversion if i == j else 1.0)` — amateurs pick the same clean
  favourite-wins scores the model likes (those biases already coincide with the grid), but down-weight
  draws by `draw_aversion` (≈0.4).
- Normalize `w`, then sharpen: `own_exact(i,j) = w(i,j)^sharpness / Σ w^sharpness` (one rival's pick
  distribution; `sharpness = config.FIELD_SHARPNESS`). Σ own_exact = 1.
- `own_toto[o]` = Σ own_exact over cells with outcome `o ∈ {home, draw, away}` (sign of i−j).

Parsimonious: a single distinct parameter (`DRAW_AVERSION`) on top of the model grid. (Clean-score and
favourite biases are already captured by the grid's high-probability cells, so no separate boosts.)

## 4. Leverage-adjusted scoreline objective (retires `toto_weight`)

Per candidate `(i,j)`, the **selection** score (the champion `leverage_score` analog, per outcome):
```
L(own) = 1 / (1 + own·(N−1))^γ                      # crowded outcomes discounted; N = pool_size
sel(i,j) = 45·P_grid(exact i,j)·L(own_exact[i,j])
         + 30·P_grid(outcome(i,j))·L(own_toto[outcome])
```
- `outcome(i,j)` = home/draw/away by sign(i−j); `P_grid` = `grid.exact` / `grid.p_{home,draw,away}`.
- The true EV (`ev`, i.e. `45·exact + 30·toto`) is kept unchanged for reporting.
- `γ = config.SCORELINE_LEVERAGE_GAMMA[risk]` (risk-keyed, mirroring champion `GAMMA`:
  `{max_ev:0.0, balanced:0.5, aggressive:1.0}`). **Pool size enters through L's denominator**
  (`own·(N−1)`), so a small pool automatically gets near-zero discount → near-chalk (this replaces the
  old pool-scaled `toto_weight`; `γ` itself is not pool-scaled).
- Behaviour: tight game → the under-owned draw (low own → high L) overtakes the crowded 1-0 when their
  grid probabilities are close → we predict the draw; clear-favourite game → modal 1-0 still wins.

## 5. Integration

- `match_ev.py`: keep `score_ev` (raw EV). Add `_leverage(own, n_rivals, gamma)` and
  `score_sel(grid, i, j, own_exact, own_toto, n_rivals, gamma)`. `topk_scorelines(grid, k, own_exact,
  own_toto, n_rivals, gamma)` ranks by `sel = score_sel(...)`, keeps `ev = score_ev(...)` for reporting.
  (Drops the `toto_weight` parameter.)
- `group_opt.optimize_group(...)`: replace the `toto_weight` plumbing with `(own_by_match, n_rivals,
  gamma)`; `cand = [topk_scorelines(grids[m], k, *own_by_match[m], n_rivals, gamma) for m in matches]`.
  The combo objective already maximizes `Σ sel + standings` — unchanged otherwise (standings still derived).
  Note: the standings term stays **raw** expected points (standings-leverage is out of scope), so the
  objective is *leverage-adjusted scorelines + raw standings*; the §6 pool-win check is what guards against
  the scoreline discount letting undiscounted standings over-anchor the picks (if it does, lower `γ`).
- `main.py`: per match, `own = field.scoreline_ownership(grid, config.DRAW_AVERSION, config.FIELD_SHARPNESS)`;
  pass `own_by_match`, `n_rivals = pool_size − 1`, `gamma = config.SCORELINE_LEVERAGE_GAMMA[risk]` into
  `optimize_group`.
- `report.py`: replace the "scoreline tilt: X% bold" line (from the retired `toto_weight`) with a short
  note that scorelines are pool-leverage-adjusted (draw-aware), and surface how many picks are draws.

## 6. Validation (pool-win evaluator as the judge)

A test/diagnostic scores two of OUR entries through the existing pool machinery — `new` (leverage
scorelines) vs `chalk` (raw-EV scorelines), champion + topscorers held equal — against the same sampled
field + worlds, and asserts `P_win(new) ≥ P_win(chalk)` (within MC noise). This closes the loop: the
heuristic is accepted only if the principled simulator agrees it helps.

## 7. Config

- `DRAW_AVERSION = 0.4` — rivals pick ~40% of the draws the model implies.
- `SCORELINE_LEVERAGE_GAMMA = {"max_ev": 0.0, "balanced": 0.5, "aggressive": 1.0}`.
- **Retire** `SCORELINE_BOLDNESS` and `scoreline_toto_weight(...)` (superseded). Update the report and
  remove/replace `tests/test_config.py::test_scoreline_toto_weight`.

## 8. Error handling
- `own` defaults to 0.0 for any cell/outcome not in the dict → `L = 1` (no discount), safe.
- `N = 1` (pool of one) → `own·(N−1) = 0` → `L = 1` → exact EV (no differentiation), correct.
- Ownership distribution always normalized; sharpen guards against all-zero (uniform fallback).

## 9. Testing (TDD)
- `test_field`: `scoreline_ownership` down-weights draw cells (1-1 own < its grid prob share), sums to 1,
  `own_toto` aggregates correctly; `draw_aversion=1.0` ⇒ pure sharpened grid.
- `test_match_ev`: `L` reduces to raw EV when `own` uniform or `N=1`; a constructed tight game where a
  low-owned 1-1 has `sel` > the high-owned 1-0 (flip), while a clear-favourite keeps 1-0; `ev` field
  unchanged.
- `test_group_opt`: still returns 6 sorted picks; objective uses `sel`; existing tests updated to the new
  signature.
- `test_pool` (validation): leverage entry's pool-win ≥ chalk entry's on a synthetic with an under-owned
  draw.
- Full suite green; real run shows a sensible, modest increase in predicted draws (not a draw-everywhere
  blowup) and the pool-win uplift.

## 10. Deliverables / retired
New: `field.scoreline_ownership`, `match_ev.score_sel`/`_leverage`. Modified: `match_ev.topk_scorelines`,
`group_opt.optimize_group`, `main.py`, `report.py`, `config.py`, `tests/{test_field,test_match_ev,
test_group_opt,test_config,test_pool}.py`. Retired: `config.SCORELINE_BOLDNESS`,
`config.scoreline_toto_weight`. No change to goals/grid/champion/tournament/topscorer/eval logic.
