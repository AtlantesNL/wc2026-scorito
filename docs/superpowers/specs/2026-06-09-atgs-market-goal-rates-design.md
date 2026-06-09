# Anytime-goalscorer market goal rates (③) — design spec

**Date:** 2026-06-09 · **Status:** approved · **Author:** R. van Bruggen + Claude

## 1. Problem
The topscorer model's core input `g90` (non-penalty goals/90) is **hand-estimated** from 2025-26 club
data. The Odds API exposes a real `player_goal_scorer_anytime` (ATGS) market for WC2026 (verified live:
72 events, 2 books × 46 selections on event 1). Replace `g90` with **market-implied per-match goal
rates** where available, falling back to the hand estimate otherwise — sharper, opponent- and
minutes-aware inputs into the same pool-win engine.

## 2. Goals / Non-goals
- Pull ATGS per match, convert P(score) → per-match goal rate `λ`, sum over a player's group games into a
  market-blended **expected group goals** that feeds EV, the goal sampler, and the field's fame model.
- **Graceful degradation:** partial or zero ATGS coverage falls back to today's hand `g90` per match;
  **no ATGS → byte-identical to today** (zero regression).
- **Non-goals (YAGNI):** group-phase ATGS only (the 72 listed events, no knockouts); flat-margin de-vig
  (no per-player overround model); name-match via normalization + a small alias map (accept partial
  coverage); no change to scorelines/champion/grid/tournament logic.

## 3. ATGS client (`scorito/data/odds.py`)
- `EVENTS_URL = ".../v4/sports/soccer_fifa_world_cup/events"`; per-event
  `.../events/{id}/odds`.
- `fetch_atgs(api_key, regions=config.ATGS_REGIONS)`: GET `/events` → list `{id, home_team, away_team}`;
  for each event GET `/events/{id}/odds?regions={regions}&markets=player_goal_scorer_anytime&oddsFormat=decimal`.
  Returns the list of per-event JSON responses (cache to `data/cache/atgs_raw.json`, already gitignored).
  `regions="eu,uk"` → ~2 credits/event × 72 ≈ 144 (free tier 500/mo).
- `parse_atgs(raw)` → `{(home_ofb, away_ofb): {normalized_player: median_price}}`. Per event: map
  `home_team/away_team` via `_ofb`; across bookmakers, for `markets[].key == "player_goal_scorer_anytime"`,
  per outcome take `player = outcome.get("description") or outcome["name"]` and skip the negative leg
  (`name in {"No","Under"}`); aggregate **median price per player** across books. (Exact outcome field —
  `name` vs `description` — confirmed against the cached feed during implementation.)

## 4. Player-name matching (`scorito/data/odds.py`)
`_norm(name)` = casefold + strip accents (`unicodedata.normalize NFKD`) + drop punctuation/extra spaces.
`ATGS_PLAYER_ALIASES = {normalized_api_name: our_candidate_name}` for the few mismatches. A candidate
matches a match's priced selection iff `_norm(candidate) == _norm(api)` (or via alias). Unmatched →
hand fallback for that match.

## 5. Market→λ blend (`scorito/model/topscorers.build_expected_goals`)
`build_expected_goals(candidates, matches, atgs_map, team_factors, margin=config.ATGS_MARGIN)` → new
candidate dicts each with `exp_goals` (expected group goals) + `goals_src ∈ {market, blend, hand}`:
- A candidate's group matches = `matches` where `c["team"] ∈ (team1, team2)` (≤3).
- **Order-agnostic match lookup:** a player's ATGS price is the same regardless of home/away, and the
  API's home/away may differ from our fixtures', so look up `atgs_map.get((h,a)) or atgs_map.get((a,h))`
  (prevents silent zero-coverage from a convention mismatch).
- Per match `m`: if the player is priced in that match's selections → `p = min(0.99, (1/price)/margin)`,
  `λ_m = −ln(1 − p)` (**includes penalties + opponent** → do *not* re-apply `team_factor`/`pen_share`).
  Else → hand fallback `λ_m = g90·start_prob·team_factor + (PEN_BONUS·pen_share)/n_matches`.
- `exp_goals = Σ λ_m`. (The pen bonus is dropped on the hand `team_factor` term — a penalty converts at a
  fixed rate regardless of opponent — so hand-only players differ <2% from today on the pen term only;
  acceptable and arguably more correct. To keep zero-regression, build_expected_goals runs **only when
  `atgs_map` is non-empty**; with no ATGS the candidates pass through untouched.)

## 6. Wire-through (backward compatible)
- `score_candidate(c, team_factors)`: if `"exp_goals" in c` → `c["exp_goals"] * TOPSCORER_MULT[pos]`
  (multiplier only); else today's `g90` path.
- `fame_score(c, team_factors)`: if `"exp_goals" in c` → `c["exp_goals"]` (rivals see the same market);
  else today's path.
- `sample_player_goals(...)`: `λ = c["exp_goals"]` if present else today's `(g90·3·start + PEN·pen_share)·tf`.

## 7. CLI / caching (`scorito/main.py`)
Opt-in (credits): `--atgs` (fetch live; requires `--odds-key`/`$ODDS_API_KEY`; caches to
`data/cache/atgs_raw.json`) and `--atgs-file PATH` (replay cached). In `run(...)`: build `atgs_map` from
fetch/file (else `{}`); after `team_factors` + `kept` are known, `if atgs_map: kept =
build_expected_goals(kept, matches, atgs_map, team_factors)`. Everything downstream (pick/engine/sampler)
already reads `exp_goals`. The key is never logged or committed.

## 8. Report (`scorito/report.py`)
Topscorer table gains a source marker (📈 market / ✍️ hand) per pick and a one-line note of how many of
the 6 are market-priced; optionally show implied P(score)/match. CSV gets a `source` detail.

## 9. Config
`ATGS_MARGIN = 1.06` (flat de-vig); `ATGS_REGIONS = "eu,uk"`.

## 10. Error handling
- Per-event fetch failure (404/timeout) → skip that event (partial coverage), warn count.
- `price ≤ 1.0` or missing → skip (hand fallback). `p` clamped to `[_, 0.99]` so `−ln(1−p)` is finite.
- Player in ATGS but not a candidate → ignored. Candidate not priced → hand fallback. Empty `atgs_map`
  → no augmentation (today's behavior).

## 11. Testing (TDD)
- `test_odds`: `parse_atgs` on synthetic raw → correct `{match: {player: median}}`; handles
  `description`-vs-`name`, skips the No leg, medians across books. `_norm`/alias matching.
- `test_topscorers`: `λ = −ln(1−p)` math (p=0.5 → 0.693); `build_expected_goals` — priced player gets
  market `exp_goals` (no `team_factor` re-applied), unpriced gets hand, mixed → `blend`, tags correct;
  `score_candidate`/`fame_score`/`sample_player_goals` use `exp_goals` when present and the **g90 path
  unchanged when absent** (backward-compat assertions).
- Integration: `--atgs-file` augments candidates; no-ATGS run identical to today.
- Full suite green.

## 12. Validation (real run)
Pull ATGS (`--atgs` or cached), sanity-check elite implied rates (Kane/Mbappé ~0.4-0.6 P(score)/match →
λ~0.5-0.9), report coverage (how many candidates market-priced), and whether the blend changes the
recommended 6 vs hand `g90`. Document in `docs/atgs-market-goal-rates-2026-06-09.md`.

## 13. Deliverables
New: `odds.fetch_atgs`/`parse_atgs`/`_norm`/`ATGS_PLAYER_ALIASES`, `topscorers.build_expected_goals`.
Modified: `topscorers.score_candidate`/`fame_score`/`sample_player_goals` (read `exp_goals`), `main.py`
(`--atgs`/`--atgs-file` + wiring), `report.py` (source marker), `config.py` (`ATGS_MARGIN`,
`ATGS_REGIONS`), `tests/{test_odds,test_topscorers}.py`, README + finding doc. Retired: nothing.
