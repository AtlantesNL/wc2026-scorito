# Reliable champion title prior (live market consensus) — design spec

**Date:** 2026-06-09 · **Status:** approved (A — live de-vigged bookmaker consensus) · **Author:** R. van Bruggen + Claude

## 1. Problem
The champion title prior blends the Monte-Carlo sim with a prior that is currently a **hand-typed**
Polymarket/Opta snapshot (`priors.MARKET`, ~8 teams). It's stale, single-source, manual, and covers few
teams — so longshots the market doesn't rate get only the MC's (inflated) estimate. Research: betting
markets are the gold standard for tournament-winner odds; Opta is largely market-derived (a correlated
cross-check, not an independent equal). The Odds API exposes a **live multi-bookmaker WC-winner outright**
(`soccer_fifa_world_cup_winner`, verified key) we already have access to — use it.

## 2. Goals / Non-goals
- Replace the hand-typed market prior with a **live, de-vigged, multi-bookmaker consensus** covering ~30
  teams, keeping **Opta as a light cross-check** and the MC as the structural backbone.
- **Broad coverage is the main win:** every real contender (not just 8) gets a true market anchor, so the
  MC's longshot over-rating (Colombia/Ecuador, seen in review) deflates naturally.
- **Minimal tuning:** keep `CHAMPION_MARKET_WEIGHT=0.5` initially; raise it (~0.65) **only if** validation
  still shows MC inflation — a documented, evidence-driven follow-up, not a blind knob-turn.
- **Non-goals (YAGNI):** no Polymarket/Kalshi API integration (correlated, marginal, more failure surface);
  Polymarket numbers remain the documented cross-check + fallback. No change to scoreline/topscorer logic.

## 3. Outright fetch + de-vig (`scorito/data/odds.py`)
- `WINNER_URL = ".../v4/sports/soccer_fifa_world_cup_winner/odds"`.
- `fetch_winner_outrights(api_key, regions=None)`: GET `WINNER_URL?regions={regions or config.ATGS_REGIONS}
  &markets=outrights&oddsFormat=decimal`. Returns the JSON (list); cache to `data/cache/winner_raw.json`
  (gitignored). ~1 request × regions ≈ 2 credits.
- `parse_winner_market(raw)` → `{team_ofb: prob}` (consensus, sums to 1):
  - For each bookmaker's `markets[key=="outrights"]`: collect `{_ofb(outcome.name): price}` for `price > 1`.
  - **Proportional de-vig per book** (robust to the long tail of unlisted minnows; Shin assumes exhaustive
    outcomes, which an outright that lists only ~30 of 48 teams is not): `inv = 1/price`, divide each by
    `Σ inv` so the book's listed teams sum to 1. (Books listing < 8 teams are skipped as too thin.)
  - **Median across books** per team (a team is included if ≥1 book lists it), then **renormalize** the
    consensus to sum 1.

## 4. Combination (`scorito/data/priors.py`)
`blended_probs(market=None)`:
- `mkt = market if market else MARKET` (live consensus when provided, else the hand-typed fallback).
- For each Opta team: `0.5·Opta + 0.5·mkt[team]` if covered, else Opta.
- **Also include market-only teams** (in the live consensus but not Opta — e.g. Morocco, Croatia): use the
  market prob directly. This is the broad-coverage benefit (real anchors for ~30 teams).
`blend_champion_probs(mc, blended_probs(market=consensus), weight=CHAMPION_MARKET_WEIGHT)` is unchanged —
but now its `market` arg covers ~30 teams, so far less residual mass is spread over uncovered teams ∝ MC,
which is what tempers the MC longshot inflation.

## 5. Wiring + caching (`scorito/main.py`)
Mirror the odds/ATGS pattern: when live odds are fetched (`--odds-key`, not `--no-odds`), also
`fetch_winner_outrights` and cache it; `--winner-file PATH` replays a cached feed. Parse to a `winner_map`
(else `{}`); pass it as `blended_probs(market=winner_map or None)` at both call sites
(`pwin = blend_champion_probs(sim["win"], blended_probs(market=winner_map))` and the `len(gteams)!=12`
fallback). Key never logged/committed.

## 6. Validation + transparency
Diagnostic logging the **live consensus vs Opta vs the Polymarket numbers** for the top ~12 (they should
agree — Spain/France ~16%, England/Portugal ~10-11%, …; wild divergence flags a parse/liquidity problem).
Then a real run confirming: the title prior is market-grounded; the previously-inflated longshots
(Colombia/Ecuador) now sit at their real (low) market level; the champion recommendation is sensible
(expected: Spain robust). If the MC still inflates non-market teams, raise `CHAMPION_MARKET_WEIGHT`→~0.65
and re-validate. Documented in `docs/reliable-title-prior-2026-06-09.md`.

## 7. Fallback + availability verification
If the outright isn't live on the free tier 2 days out (or the fetch fails), `parse_winner_market` returns
`{}` → `blended_probs(market=None)` → the hand-typed Opta+MARKET (today's behavior). **Zero regression.**
As with ATGS, verify with a 10-second live check before leaning on it.

## 8. Config / error handling
- `regions` reuses `config.ATGS_REGIONS` ("eu,uk"). No new constant unless §6 raises `CHAMPION_MARKET_WEIGHT`.
- Per-book overround always > 1 (de-vig divides down); a book with < 8 listed teams is skipped; empty feed
  → `{}` → fallback. Team-name variants the feed uses but `_ofb` misses fall to "market-only" with their
  own (correct) prob, or are simply uncovered (Opta/MC) — discovered + mapped during the build, like ATGS.

## 9. Testing (TDD)
- `test_odds`: `parse_winner_market` on synthetic raw (2 books, an `outrights` market with an overround) →
  de-vigged consensus sums to 1, favourite ranked first, median across books, `_ofb` mapping applied,
  thin books skipped.
- `test_priors`: `blended_probs(market={...})` uses the live consensus (Opta team averaged; market-only
  team included at its market prob); `blended_probs()` (no arg) is unchanged (hand-typed fallback).
- Integration: `--winner-file` feeds the consensus into `pwin`.
- Full suite green; real-run validation per §6.

## 10. Deliverables
New: `odds.WINNER_URL`/`fetch_winner_outrights`/`parse_winner_market`, `--winner-file`/auto-fetch wiring,
`blended_probs(market=...)` parameter, finding doc. Modified: `scorito/data/odds.py`, `scorito/data/priors.py`,
`scorito/main.py`, `tests/{test_odds,test_priors}.py`, README. Retired: nothing (`MARKET`/Opta kept as the
fallback + cross-check).
