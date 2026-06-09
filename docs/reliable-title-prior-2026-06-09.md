# Reliable champion title prior (live market consensus) — finding (2026-06-09)

## What
Replaced the hand-typed champion title prior (~8 teams) with a **live, de-vigged, multi-bookmaker
WC-winner outright consensus** from The Odds API (`soccer_fifa_world_cup_winner`, `markets=outrights`,
eu+uk books). Proportional de-vig per book → median across books → renormalized consensus. Opta is kept
as a cross-check, the Monte-Carlo as the backbone; falls back to the hand-typed prior if the feed is
unavailable. Replay via `--winner-file` (auto-fetched + cached on a live `--odds-key` run).

## Live consensus vs Opta vs Polymarket (validation)
The de-vigged bookmaker consensus (54 teams covered) matches the prediction market almost exactly:

| Team | bookmaker consensus | Opta | Polymarket |
|---|---|---|---|
| Spain | 16.4% | 16.1% | 16% |
| France | 15.3% | 13.0% | 16% |
| England | 10.3% | 11.2% | 11% |
| **Portugal** | **9.7%** | 7.0% | 10% |
| Argentina | 8.2% | 10.4% | 8% |
| Brazil | 8.2% | 6.6% | 8% |
| Germany | 5.4% | 5.1% | 5% |
| Netherlands | 4.3% | 3.6% | 4% |

Spot-on agreement validates the de-vig + name-mapping (no garbled teams, favourites on top, sums to 1).
Notably it confirms **Portugal ~10%** — which Opta under-rated at 7% — and now anchors **54 teams** (vs the
8 hand-typed), so every contender has a real market prior instead of the Monte-Carlo's estimate.

## Effect on the champion pick
| | before (hand-typed 8) | after (live 54-team consensus) |
|---|---|---|
| Recommended | Spain | **Spain** (unchanged, robust) |
| Argentina (dart) | 11.4% outright | 11.4% outright, Win-pool 10.6% |
| Colombia outright | 4.2% (pure-MC, no anchor) | **3.3%** (market-tempered) |
| Portugal outright | 6.4% | 7.0% (proper 10% anchor) |

The live market **tempered the Monte-Carlo's longshot over-rating** (Colombia 4.2→3.3% once it carries its
real, low market prob). Colombia still shows ~8.5% Win-pool (#3), but that is dominated by the **base
pool-win** (the chance you finish 1st on scorelines/standings/topscorers — *common to every champion
pick*), plus a small bonus from its 3.3% title chance; it is **not** the recommendation. The argmax +
SE-floor tie-break correctly takes **Spain**, so `CHAMPION_MARKET_WEIGHT` was **kept at 0.5** — no
over-tuning was warranted.

## Verdict
The champion prior is now sourced from the **most reliable available signal** — a live, multi-bookmaker,
de-vigged consensus — refreshed on every keyed run, covering 54 teams, and matching the sharp market.
Opta and the hand-typed Polymarket numbers remain as cross-check + fallback. The recommendation (Spain
robust, Argentina dart) is unchanged and now rests on live market data rather than a hand-typed snapshot.

## How to run
`python -m scorito.main --odds-key "$ODDS_API_KEY" --atgs --risk balanced` auto-fetches + caches the
outright; replay offline with `--winner-file data/cache/winner_raw.json` (no key/credits). Re-pull at lock.
