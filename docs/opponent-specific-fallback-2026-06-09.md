# Opponent-specific topscorer hand-fallback (easy-opener tilt fix) — finding (2026-06-09)

## Why
With anytime-goalscorer (ATGS) odds only priced for each team's *opening* game 2 days out, a player's other
two group games fell to a hand estimate that used the team's **group-average** scoring factor — which the
easy opener itself inflated. So Germany's `team_factor=1.94` (boosted by a Curaçao blowout) was applied to
Germany's *tougher* games (Ivory Coast, Ecuador), over-stating them. Result: **Wirtz**, a midfielder
(16× multiplier) in a soft group, was the model's #1 topscorer despite a modest 0.23 g90 — an artifact, as
the user spotted.

## Fix
In `topscorers.build_expected_goals`, an unpriced match now uses the **opponent-specific** team scoring —
the team's expected goals *in that specific match* (already computed by the goals model) ÷ the tournament
average — instead of the one group-average number for all three games. Market-priced games and the position
multiplier are unchanged; backward-compatible (no `match_lams` → group-average, byte-identical).

## Before → after (topscorer EV)
| | BEFORE (group-average) | AFTER (opponent-specific) |
|---|---|---|
| #1 | **Wirtz 25.9** | **Kane 25.8** |
| | Kane 24.6 | Wirtz 22.0 |
| | Haaland 24.0 | Mbappé 21.5 |
| | Mbappé 20.8 | Haaland 20.2 |
| | Yamal 19.9 | Lautaro 19.4 |

- **Wirtz 25.9 → 22.0**: his tough unpriced games (Ivory Coast, Ecuador) now use Germany's *real* (lower)
  expected goals there instead of the Curaçao-boosted average. He drops from #1 to #2 — still a defensible
  high-multiplier MID pick, but no longer over-rated.
- **Kane rises 24.6 → 25.8** and leads: his unpriced games are vs minnows (Ghana, Panama), correctly scored
  *high* by opponent-specific λ; his tough opener (Croatia) was already market-priced.
- Other easy-opener players deflate (Haaland 24→20.2, Yamal 19.9→18.6); the ordering is now driven by real
  per-opponent scoring, not by which team had one blowout in its priced opener.

## Shipped
Champion unchanged (Spain robust). Engine-selected six: Wirtz, Kane, Mbappé, Lautaro, Haaland, Yamal —
with Kane now the top-EV pick and Wirtz a properly-valued #2. 102 tests green.

## Note
This further reduces (does not eliminate) the need to re-pull at lock: once matchdays 2-3 are
market-priced, those games use real ATGS odds directly and the hand fallback isn't used at all.
