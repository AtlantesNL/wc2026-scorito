# Champion full-tournament Monte-Carlo — design spec

**Date:** 2026-06-09 · **Status:** approved (Approach A — pragmatic MC) · **Author:** R. van Bruggen + Claude

## 1. Problem

`P(win)` for the champion pick is a **static hand-typed dict of 11 teams** (`scorito/data/priors.py`:
Opta + two market numbers, frozen 4 June). It ignores 37 teams, isn't draw-aware, and isn't
consistent with the model's own match λ's. Replace it with a **full-tournament Monte-Carlo** that
simulates group → knockout from the same λ engine, yielding live, draw-aware `P(win)` for **all 48
teams** (plus advancement probabilities), then **blends** that with the market/Opta odds.

## 2. Goals

- `P(win)` for all 48 teams from a seeded Monte-Carlo of the real 2026 bracket.
- Reuse existing primitives: group grids (odds/Elo → `build_grid`), `_sample_scores`, `_rank_table`,
  `goals_from_elo`.
- Blend MC (backbone) with the market/Opta prior (sharpening) — decision locked in brainstorming.
- Bonus output: per-team **advancement probabilities** (reach R16/QF/SF/Final) for the report ("path difficulty").
- Feed the existing champion **leverage** layer unchanged.

## 3. Non-goals (YAGNI)

- **No** official FIFA 495-row third-place table — use constraint-matching against openfootball's
  per-slot allowed-group sets (champion-prob impact of exact slotting is second-order).
- **No** extra-time/penalty scoreline model — KO ties resolve by `P(advance) = p_win + ½·p_draw`.
- **No** rework of knockout-phase scoreline/topscorer picks (separate future item).
- **No** KO-specific odds (none exist free) — KO matchups use the Elo path.

## 4. Architecture

```
scorito/model/bracket.py      # NEW: load+parse openfootball KO tree; token resolution; 3rd-place matching
scorito/model/tournament.py   # NEW: Elo advance matrix + Monte-Carlo -> P(win) + advancement (all 48)
scorito/data/priors.py        # +blend_champion_probs(mc, market, weight); keep OPTA/MARKET + blended_probs()
scorito/model/champion.py      # recommend_champion(pwin, pool_size, risk) now TAKES a probs dict
scorito/main.py                # collect 72 group grids -> simulate -> blend -> champion; advancement -> report
scorito/report.py              # champion table gains advancement columns (R16/QF/SF/Final %)
scorito/config.py              # +CHAMPION_MARKET_WEIGHT = 0.5 ; reuse MC_SIMS for tournament sims
```
`bracket` = pure structure/assignment (no randomness). `tournament` = sampling. `champion` = leverage
on whatever probs it's handed.

## 5. Bracket data (openfootball `worldcup2026.json`)

104 matches = 72 group + 32 KO. KO matches carry `num`; tokens:
- `"1A"`/`"2B"` → group A 1st / group B 2nd.
- `"3A/B/C/D/F"` → a third-place slot with allowed groups `{A,B,C,D,F}` (8 such slots in R32).
- `"W{n}"` / `"L{n}"` → winner / loser of match `n`.

Match numbering (verified): R32 = 73–88, R16 = 89–96, QF = 97–100, SF = 101–102; **Final** (`W101 vs
W102`) and **third-place** (`L101 vs L102`) have `num=None` → identified by `round`. The champion MC
walks 73→102 then the Final; the third-place playoff is **not simulated** (irrelevant to `P(win)`).

## 6. `bracket.py`

- `load_bracket(fixtures_src) -> Bracket`: read the raw json, return the 32 KO matches as ordered
  nodes, each with `num`, `round`, and parsed `team1`/`team2` references
  (`GroupPos(pos, group)` | `ThirdSlot(allowed:set)` | `WinnerOf(num)` | `LoserOf(num)`).
- `qualify_thirds(third_place_teams_with_stats) -> list[8]`: rank the 12 third-placed teams by
  `(pts, gd, gf)` (ties via rng) → best 8.
- `assign_thirds(qualified_thirds, third_slots) -> {slot_index: team}`: bipartite match via
  `scipy.optimize.linear_sum_assignment` on a cost matrix (`0` if the team's group ∈ slot.allowed,
  else large). If the min-cost assignment still violates a constraint (should never happen for valid
  FIFA sets), fall back to a greedy feasible assignment and `warnings.warn`.

## 7. `tournament.py`

`advance_matrix(teams, elo) -> {(A,B): p_A_advances}`: for each unordered pair, `goals_from_elo(elo[A],
elo[B])` (neutral) → `build_grid` → `p = grid.p_home + 0.5*grid.p_draw`; store `P[(A,B)]=p`,
`P[(B,A)]=1-p`. ~1.1k grids, cached once. (Uses the host-boosted `elo_map` from `main.py`; hosts thus
keep a mild edge in KO — documented, minor.)

`simulate(gteams, group_matches, group_grids, elo, bracket, sims=config.MC_SIMS, seed=0) -> dict`:
1. `sampled = _sample_scores(all_group_match_keys, group_grids, sims, rng)`.
2. Per sim `s`: build the 12 group tables (`_rank_table` with that sim's h2h) → 1st/2nd/3rd/4th.
3. Rank the twelve 3rd-place teams → best 8 (`bracket.qualify_thirds`); `assign_thirds` to the R32 slots.
4. Walk matches 73→102 then Final: resolve each side (group token via the tables / 3rd-slot map, or
   `W{n}`/`L{n}` from a `winners`/`losers` dict filled as we go), draw `u<P[(t1,t2)]` → winner.
5. Tally: `win[champion]++`; for each team record the deepest round reached.
Return `{"win": {team: p}, "advance": {team: {"r16","qf","sf","final","win": p}}}` (counts / sims).

Reuses `_sample_scores`/`_rank_table` from `group_sim`. Per-sim pure-Python loop over 20k is a few
seconds (advance probs are O(1) lookups).

## 8. The blend — `priors.blend_champion_probs(mc, market, weight)`

`market` = existing `blended_probs()` (Opta+market, ~11 teams, genuine probs summing to ≈0.86).
- `residual = max(0, 1 − Σ market)`; spread it over the uncovered teams **∝ mc**:
  `market_full[t] = market[t]` if covered, else `residual · mc[t] / Σ_{uncovered} mc`.
- `pwin[t] = weight·market_full[t] + (1−weight)·mc[t]` (sums to 1).
- `weight = config.CHAMPION_MARKET_WEIGHT` (default **0.5**; `0`=pure MC, `1`=market-anchored).
Edge: if `Σ market ≥ 1`, set residual 0 and renormalize `market_full` over covered teams only.

## 9. Integration & output

- `champion.recommend_champion(pwin, pool_size, risk)` — accept the blended `pwin` dict (was internal
  `blended_probs()`); `est_shares`/`leverage_score` unchanged, now over all 48.
- `main.py`: accumulate `all_group_grids` across the group loop; `bracket = load_bracket(fixtures_src)`;
  `sim = tournament.simulate(...)`; `pwin = blend_champion_probs(sim["win"], blended_probs(), config.CHAMPION_MARKET_WEIGHT)`;
  `recommend_champion(pwin, …)`; pass `sim["advance"]` into `RunResult`.
- `report.py`: champion table adds **R16/QF/SF/Final %** columns from `sim["advance"]`.

## 10. Error handling

- Missing Elo → 1500 (existing `get_elo` behaviour) → advance matrix still defined.
- Unresolvable bracket token → raise a clear `ValueError` (structure is fixed; fail fast).
- Infeasible third-place matching → greedy fallback + `warnings.warn` (never expected).
- Seeded rng for determinism (as in `position_probs`).

## 11. Testing (TDD, network-free)

- `test_bracket`: parses the 32 KO matches (16 R32 with group tokens + 8 third-slots; R16+ `W{n}` links);
  `assign_thirds` returns a constraint-valid assignment on a hand case; a feasibility check that every
  8-of-12 third-place combination admits a valid assignment against the real slot sets.
- `test_tournament`: dominant-team toy bracket → `P(win)=1`; `advance_matrix` monotonic in Elo &
  complementary (`P[A,B]+P[B,A]=1`); `Σ P(win) ≈ 1`; seed-deterministic.
- `test_priors`: `blend_champion_probs` — `w=0`→mc, `w=1`→market_full; sums to 1; uncovered teams get
  mass ∝ mc.
- `test_champion`: existing tests adapted to `recommend_champion(pwin, …)`; leverage ordering unchanged
  for a fixed pwin.
- `test_report`/smoke: champion rows carry advancement; `main` run yields 48-team probs.

## 12. Performance
Advance matrix (~1.1k grids, ~1s) + `MC_SIMS` (20k) tournament sims ≈ a few seconds, on par with
`calibrate`. Sim count reuses `config.MC_SIMS`.

## 13. Deliverables
`scorito/model/bracket.py`, `scorito/model/tournament.py`, edits to `priors.py`/`champion.py`/`main.py`/
`report.py`/`config.py`, and `tests/test_bracket.py` + `tests/test_tournament.py` (+ adapted
`test_champion.py`). No change to the goals/grid/group/topscorer/eval code.
