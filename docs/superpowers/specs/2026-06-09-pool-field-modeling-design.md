# Pool/field modeling — design spec (champion slice)

**Date:** 2026-06-09 · **Status:** approved (Approach A — parametric field + nested Monte-Carlo) ·
**Author:** R. van Bruggen + Claude

## 1. Problem

Differentiation is currently two ad-hoc heuristics — `scoreline_toto_weight`/`SCORELINE_BOLDNESS`
(scorelines) and `est_shares`/`leverage_score`/`GAMMA` (champion). Replace them with **one
principled objective: maximize P(our entry finishes 1st in the pool)**, computed by simulating
both the tournament *and* the rival field.

This spec covers the **first sub-project (champion slice)**: build the reusable pool-win **engine**
(field model + evaluator) and apply it to the **champion** pick (a single choice → trivial
optimizer), replacing `leverage_score`. Scorelines and topscorers are later sub-projects that reuse
the same engine with harder optimizers.

## 2. Evidence-based posture (why this design, not blanket contrarianism)

Pool-strategy research (NFL pick'em, March-Madness brackets, DFS) is consistent: optimize **EV
relative to the field**; **pool size** sets how contrarian to be (small pools → mostly favourites +
*selective* leverage; only thousand-entry fields warrant aggressive contrarianism); leverage pays
**only on over-owned outcomes**, and over-doing it backfires. For a **~40-person amateur** pool with
a **win-it** payout, the optimum is an **EV backbone with surgical leverage on the most over-owned
spots** — the champion being #1. The model must *find* that balance, not impose contrarianism; for a
40-person chalky field it should land **close to EV** with a few targeted deviations. (Sources in
`docs/` brainstorm log / commit message.)

## 3. Goals

- A **field model**: generate `N = pool_size − 1` plausible rival entries from chalk-weighted
  distributions with one tunable **sharpness** knob (default = chalky).
- A **pool-win evaluator**: `P(our entry finishes strictly 1st)` via nested Monte-Carlo over sampled
  tournament *worlds*, scoring every entry with `eval/metrics`.
- A **champion optimizer**: choose the champion maximizing P(win-pool), holding our other picks at the
  current model output. Replaces `leverage_score` as the recommendation; report shows P(win-pool) per
  top candidate.
- Reuse the goals grids, the champion bracket sim, and `eval/metrics`. One new piece: a per-player
  group-goal sampler.

## 4. Non-goals (YAGNI)

- **Not** optimizing scorelines or topscorers yet (separate sub-projects; this slice holds them fixed).
- **No** payout-curve modeling beyond "win it" (P(1st)); top-k is a later option.
- **No** calibration of the field model to real pool data (none exists) — it's an explicit, tunable
  assumption.
- Player group-goals are sampled **independently** of the world's exact team scorelines (a documented
  approximation; topscorers are a minor, equally-applied component in this slice).

## 5. Architecture

```
scorito/model/field.py     # NEW: generate N rival entries (chalk-weighted, sharpness knob)
scorito/model/pool.py      # NEW: world sampler hooks + nested-MC evaluator + champion optimizer
scorito/model/topscorers.py# +sample_player_goals(candidates, team_factors, rng, sims) [per-world goals]
scorito/config.py          # +FIELD_SHARPNESS (chalky default), +POOL_WIN_SIMS
scorito/main.py            # champion recommendation via pool-win optimum; pass P(win-pool) to report
scorito/report.py          # champion table: add P(win-pool) column; note the field assumption
tests/test_field.py, tests/test_pool.py
```
`field` = pure generative sampling (rng-seeded). `pool` = the evaluator/optimizer. The champion
bracket walk is reused from `tournament` (refactor its per-world body into a reusable
`sample_champion(...)` if needed).

## 6. Entry & scoring

An **entry** = `{scorelines: {(home,away): (h,a)} ×72, champion: team, topscorers: [6 dicts]}`.
Group **standings are derived** from the entry's scorelines (Scorito builds the table from your
scores), so they're not a separate pick. Scoring an entry in a sampled **world** (actual scores +
actual champion + actual per-player goals), reusing `eval/metrics`:
`total = Σ match_points(72) + Σ standings_points(12 groups) + 250·[champion==world_champ] + topscorer_points`.
An entry's *predicted* standings are computed once (from its scorelines); the world's *actual*
standings once per world.

## 7. World sampler (`pool`, reusing existing simulators)

Per world `w` (seeded): (1) sample all 72 group scores from the grids (`_sample_scores`); (2) build
the 12 actual group tables (`_rank_table`); (3) walk the bracket to a **world champion** (reuse the
`tournament` per-world logic / Elo advance matrix); (4) sample per-player group goals via
`sample_player_goals`: for each candidate, `goals ~ Poisson(λ)` with
`λ = (g90·3·start_prob + PEN_BONUS·pen_share)·team_factor` (consistent with the topscorer EV model).

## 8. Field model (`field.generate_field`)

`generate_field(N, market_pwin, scoreline_topk, topscorer_pool, sharpness, rng) -> [entry]`. Each
rival entry:
- **Champion** ~ categorical ∝ `market_pwin[t] ** sharpness` (chalky ⇒ piles on favourites).
- **Scorelines**: per match, pick from the top-k candidate scorelines with weight ∝
  `exact_prob ** sharpness` (chalky ⇒ concentrates on the modal 1-0/1-1).
- **Topscorers**: sample 6 (no dup) from the candidate pool with weight ∝ `EV ** sharpness` (chalky ⇒
  the market top-6). `sharpness = config.FIELD_SHARPNESS` (default tuned so a chalky 40-person field
  clusters realistically; one knob).

## 9. Evaluator + champion optimizer (`pool`)

`pool_win_prob(our_entry, field, world_sampler, W) -> float` and the champion sweep, with an efficient
decomposition (only the champion varies in this slice):
1. Sample field once (§8); precompute each rival's **predicted standings** + topscorer picks.
2. For `w` in `W` worlds: sample the world (§7); compute `champ_w`; our fixed non-champion score
   `base_w` (scorelines+standings+topscorers); each rival's total
   `rival_base[r,w] + 250·[rival_champ[r]==champ_w]` → `max_rival_w`.
3. For each candidate champion `c`: `P(win|c) = mean_w( base_w + 250·[champ_w==c] > max_rival_w )`.
   Recommended champion = argmax; report P(win) for the top few. (Strict `>`; report tie rate.)

This makes the champion optimizer almost free (one vectorized sweep over candidates on cached
per-world arrays), and the same `base_w`/`max_rival_w` machinery generalizes to the later
scoreline/topscorer optimizers.

## 10. Config

`FIELD_SHARPNESS = 2.0` — the exponent on each component's chalk weight: `1.0` = rivals pick ∝ the
true probability, higher = chalkier. `2.0` is a deliberately chalky amateur-field prior (above the
~1.4 implied by the old `est_shares` temp 0.7). Because it is an **assumption with no data behind it**,
the champion recommendation is **sensitivity-checked** across `sharpness ∈ {1.5, 2.0, 3.0}` and only
acted on where it is stable (a flip across that range is reported, not silently chosen). ·
`POOL_WIN_SIMS = 5000` (worlds; perf vs. noise).

## 11. Integration & output

`main` computes the pool-win-optimal champion (sweep over the realistic contenders, e.g. teams with
market P(win) above a small floor, plus our current leverage pick) and makes it the recommendation;
the report's champion table gains a **P(win-pool) %** column and a one-line note that it assumes a
chalky ~40-person field (`FIELD_SHARPNESS`). `leverage_score`/`est_shares` are kept for reference/
display but no longer drive the pick. The pool-win sim runs once per `main` invocation (~seconds).

## 12. Error handling
Seeded rng (determinism). Degenerate field (N=0 / tiny pool) → P(win)=1 trivially, handled. Candidate
champions restricted to a sensible set (market floor) to bound the sweep. Missing market prob → use
the MC `sim["win"]`.

## 13. Testing (TDD, network-free)
- `test_field`: chalky sharpness ⇒ champion ownership concentrates on favourites (top team most-picked);
  sharpness→0 ⇒ near-uniform; entries well-formed (72 scorelines, 6 distinct topscorers); seed-deterministic.
- `test_pool`: on a tiny synthetic (few teams, small bracket, 2-3 rivals) — (a) an entry that dominates
  on EV and isn't over-owned has higher P(win) than a clone of the chalk; (b) `Σ` sanity: P(win)∈[0,1],
  seed-deterministic; (c) the efficient champion sweep equals a brute re-score; (d) **selective-leverage
  property**: when the whole field is on favourite X, switching our champion off X to a near-as-strong
  Y *raises* P(win) (the core thesis), while in a 1-rival pool the EV pick stays best.
- `test_main`/smoke: champion recommendation + P(win-pool) column present on a full run.

## 14. Performance
`W≈5000` worlds × (72 samples + bracket walk + N≈39 rival scorings). Scoring is the cost; vectorize
`match_points`/standings over numpy arrays where needed. Target ≈ the champion-MC runtime (seconds–
tens of seconds). `POOL_WIN_SIMS` tunable.

## 15. Deliverables
`scorito/model/field.py`, `scorito/model/pool.py`, `sample_player_goals` in `topscorers.py`, edits to
`config.py`/`main.py`/`report.py`, `tests/test_field.py` + `tests/test_pool.py`. No change to the
goals/grid/group/eval code; `tournament` may gain a reusable single-world `sample_champion` helper.
