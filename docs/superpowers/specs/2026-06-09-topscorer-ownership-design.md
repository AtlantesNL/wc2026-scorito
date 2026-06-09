# Topscorer ownership (fame bias) — design spec (Approach B)

**Date:** 2026-06-09 · **Status:** approved (B — engine-driven greedy selection) · **Author:** R. van Bruggen + Claude

## 1. Problem
Topscorers are 6 concentrated, high-variance, 4×-multiplier picks. The field over-owns famous
attackers and under-owns high-multiplier DEF/GK ("mostly strikers + a flier" — confirmed by the pool
owner). Today we pick by EV with a crude `TOPSCORER_DEF_RESERVE` slot-reservation, and the pool-win
field models rivals as EV-weighted — i.e. as if they *correctly* value the defender multiplier, which
erases the bias we want to exploit. Make topscorer selection **pool-win-driven** against a realistic
fame-biased field.

## 2. Goals / Non-goals
- Model the field's topscorer ownership as **fame-weighted** (rivals chase goals, ignore the position
  multiplier) so attackers are over-owned and high-multiplier DEF/GK under-owned.
- Select our 6 to **maximize P(finishing 1st)** via the existing pool-win engine (greedy + swap), not a
  per-candidate heuristic — capturing the joint portfolio (EV floor + leverage + no stacking correlated
  defenders).
- **Validate** the uplift vs the EV+reserve `pick_topscorers` baseline through `score_field`; report it
  honestly (expect a modest real edge; engine decides).
- **Non-goals (YAGNI):** no champion↔topscorer iteration (champion chosen first, topscorers under it —
  additively near-separable); no new tunable; no change to scoreline/champion/grid/tournament logic
  beyond consuming the realistic field. `pick_topscorers`+reserve stays as the fallback (no full pool)
  and the `max_ev` path.

## 3. Fame field model
New `topscorers.fame_score(c, team_factors)` = `score_candidate` **without** the position multiplier:
```
fame_score(c, tf) = (c["g90"]*3*c["start_prob"] + PEN_BONUS*pen_share) * tf.get(c["team"], 1.0)
```
`main` builds the field's pool as `ts_field_pool = [(c, fame_score(c, tf)) for c in kept]` and passes it
(instead of the EV-weighted `ts_pool`) to **both** `pool_win_champion` and `pool_win_topscorers`.
`generate_field` is unchanged — it samples 6 without replacement weighted by `fame^FIELD_SHARPNESS`, so
attackers dominate and the occasional lower-fame pick is the "flier". Our own EV/scoring still uses
`score_candidate` (with the multiplier). (This also makes the champion eval's rival field more realistic.)

## 4. `pool.pool_win_topscorers` — engine-driven greedy selection

**Pure core** (fully unit-testable, no sampling):
```
def greedy_topscorers(our_fixed, max_rival, points_by_name, n_slots):
    # our_fixed[W], max_rival[W] numpy; points_by_name {name: ndarray(W)} = multiplier * goals.
    # P(win | picks) = mean(our_fixed + sum_picked points > max_rival).
    # 1) greedy forward-select n_slots names maximizing P(win); 2) coordinate-ascent swap pass
    #    (replace each held pick with the best alternative) until no strict improvement.
    # Returns (picked_names: list, pool_win: float). Deterministic (ties -> first by dict order).
```

**Wrapper** (samples worlds + one field at `FIELD_SHARPNESS`, reuses `score_field`):
```
def pool_win_topscorers(our_entry, our_champion, candidates, gteams, group_matches, grids, elo,
                        bracket, team_factors, champion_probs, scoreline_choices, ts_field_pool,
                        pool_size, n_slots=config.TOPSCORER_SLOTS, seed=0, sims=config.POOL_WIN_SIMS,
                        bonus=config.CHAMPION_BONUS) -> (picks, pool_win):
    worlds = sample_worlds(... candidates ...)                       # pgoals covers all candidates
    field  = generate_field(pool_size-1, scoreline_choices, champion_probs, ts_field_pool,
                            FIELD_SHARPNESS, rng(seed+1))
    base_excl, rival_base, rival_champ, champ_w = score_field(dict(our_entry, topscorers=[]), field, worlds, ...)
    max_rival = (rival_base + bonus*(rival_champ[:,None]==champ_w[None,:])).max(0)   # -inf if no field
    our_fixed = base_excl + bonus*(champ_w == our_champion)
    pgoals_arr = {n: array_over_worlds(w["pgoals"][n]) for n in worlds[0]["pgoals"]}
    points = {c["name"]: TOPSCORER_MULT[c["position"]] * pgoals_arr[c["name"]] for c in candidates}
    names, pwin = greedy_topscorers(our_fixed, max_rival, points, n_slots)
    picks = [dict(by_name[n], ev=round(score_candidate(by_name[n], team_factors), 3)) for n in names]
    return picks, pwin
```
Scoring our topscorers with empty picks gives `base_excl` (scorelines+standings) cleanly; the field's
own topscorers are already in `rival_base`. Each greedy/swap evaluation is one O(W) vector compare, so
6 slots × ~30 candidates × a couple passes is fast at 15k worlds.

## 5. Integration (`main.py`) + risk
In the `len(gteams)==12` block, after the champion is chosen:
- build `ts_field_pool` (fame) and pass it to `pool_win_champion` (replacing the EV `ts_pool`);
- then, for **balanced/aggressive**, `topscorers, ts_pool_win = pool.pool_win_topscorers(dict(our_entry,
  champion=best), best, kept, …, ts_field_pool, pool_size, seed=seed)` and rebuild `RunResult.topscorers`;
- for **max_ev**, keep the `pick_topscorers` result (pure EV).
`our_entry` for the champion step still uses the EV-baseline topscorers (champion first, then topscorers
under the chosen champion — no iteration). Put `ts_pool_win` in `meta` for the report.

## 6. Validation
Compute `pool_win` for the engine-selected 6 and for the `pick_topscorers` baseline (same worlds/field,
champion fixed) and log the delta (real-run diagnostic, like the scoreline calibration). Ship the engine
picks only if the delta is ≥0 within MC noise; otherwise document and fall back to EV. Result written to
`docs/topscorer-ownership-calibration-2026-06-09.md`.

## 7. Config / error handling
- No new constant. `TOPSCORER_DEF_RESERVE` retained (fallback + max_ev via `pick_topscorers`).
- No field (`pool_size<=1`) → `max_rival = -inf` → greedy reduces to EV-greedy (picks highest-points
  names); safe. Fewer candidates than slots → pick all. `score_candidate`/`fame_score` unchanged for
  candidates missing `pen_share` (existing default logic).

## 8. Testing (TDD)
- `test_topscorers`: `fame_score` drops the multiplier (a DEF and ATT with equal expected goals get equal
  fame, but the DEF's `score_candidate` is 4× the ATT's).
- `test_field`: rival topscorer ownership under fame weights over-owns attackers — a top striker is picked
  by more of the field than a same-EV defender.
- `test_pool`: `greedy_topscorers` on synthetic arrays picks an under-owned high-multiplier player whose
  goals land in worlds where `max_rival` is beatable over a commoditized one; reduces to top-points
  greedy when `max_rival=-inf`; incremental sum == `topscorer_points` re-score; deterministic by order.
- Integration: balanced main path returns 6 squad-validated picks via the engine; `max_ev` unchanged.
- Full suite green; real run shows the engine leaning into under-owned DEF/GK with a logged pool-win
  delta vs baseline.

## 9. Deliverables / retired
New: `topscorers.fame_score`, `pool.greedy_topscorers`, `pool.pool_win_topscorers`. Modified: `main.py`
(fame field pool + topscorer optimization), `report.py` (note engine-selected, surface pool-win delta),
`tests/{test_topscorers,test_field,test_pool}.py`, README. Retired: nothing (`TOPSCORER_DEF_RESERVE`
kept for fallback/max_ev).
