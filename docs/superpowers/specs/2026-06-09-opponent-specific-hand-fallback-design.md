# Opponent-specific topscorer hand-fallback (easy-opener tilt fix) — design spec

**Date:** 2026-06-09 · **Status:** approved (A — fix inside build_expected_goals only) · **Author:** R. van Bruggen + Claude

## 1. Problem
`topscorers.build_expected_goals` blends ATGS-market goal rates (where a match is priced) with a hand
fallback (where it isn't). The hand fallback is `g90 · start_prob · team_factor`, where `team_factor` is
the team's **group-average** scoring. When only the *easy opener* is market-priced (the reality 2 days
out), the player's *tougher* group games fall to the hand fallback — but with the **group-average** factor
that the easy opener itself inflated. Concretely: Germany's `team_factor=1.94` (boosted by the Curaçao
blowout) is applied to Germany-vs-Ivory-Coast and Germany-vs-Ecuador, over-stating them. This inflates
easy-opener players — Wirtz lands at #1 (EV 25.9) on `exp_goals≈1.62`, with ~0.38 of each tough game
coming from the Curaçao-boosted factor.

## 2. Goals / Non-goals
- For a **hand-fallback** match, use the **opponent-specific** team scoring — the team's expected goals in
  *that specific match* (already computed by the goals model) ÷ the tournament average — instead of the
  group average. So a tough game uses the team's real (lower) expected goals there.
- **Non-goals (YAGNI):** only `build_expected_goals` (the market-blend path, where the mixing creates the
  tilt) — **not** the pure-hand/no-ATGS path (it's symmetric: no game is singled out, so no tilt). No
  change to market-priced matches, the multiplier, or any other logic. Backward-compatible.

## 3. The fix (`scorito/model/topscorers.build_expected_goals`)
New optional params `match_lams=None, avg_lam=None`. For a hand-fallback match `(h, a)`:
```
if match_lams and avg_lam:                       # opponent-specific
    lam = match_lams.get((h, a))                 # (λ_home, λ_away) for this exact match
    team_lam = lam[0] if c["team"] == h else lam[1]
    factor = team_lam / avg_lam
else:                                            # backward-compatible: group-average
    factor = team_factors.get(c["team"], 1.0)
total += c["g90"] * c["start_prob"] * factor + PEN_BONUS * pen_share / n
```
`(h, a)` comes from the candidate's matches (built from the same `matches` list as `match_lams`), so the
key aligns directly; if a lookup misses, fall back to `team_factors` (defensive). Market-priced matches and
the pen term are unchanged.

## 4. Wiring (`scorito/main.py`)
The group loop already computes `l1, l2 = expected_goals(m, odds_map, elo_group)` per match. Capture them:
`match_lams[(m.team1, m.team2)] = (l1, l2)` (init `match_lams = {}` beside `all_grids`). `avg_lam` is the
existing `avg = sum(means.values())/len(means)` (the same tournament-average `team_factor` divides by).
Pass both into the call: `build_expected_goals(kept, matches, atgs_map, team_factors, match_lams=match_lams,
avg_lam=avg)`.

## 5. Validation (real run)
Re-run with the cached odds/ATGS/winner files and confirm: Wirtz's tough games (Ivory Coast, Ecuador) drop
from ~0.38 to their opponent-specific level (~0.2), his `exp_goals` falls ~1.6→~1.3 (EV ~25.9→~20.6), and
**Kane (24.6) overtakes him** — the corrected ordering. Check the rest of the six shift sensibly (other
easy-opener players like Yamal deflate; tough-opener players like Kane/Bellingham unaffected or rise
relatively). Document before/after in `docs/opponent-specific-fallback-2026-06-09.md`.

## 6. Error handling / backward-compat
- `match_lams=None` (or `avg_lam` falsy) → the group-average `team_factor` path, identical to today.
- A missing `match_lams[(h,a)]` lookup → `team_factors` fallback for that match.
- `avg_lam > 0` always (mean of positive per-match λ); guard against 0 by treating falsy as "no override".

## 7. Testing (TDD)
- `test_topscorers`: `build_expected_goals` with `match_lams`/`avg_lam` uses opponent-specific factors per
  match (a high-λ game and a low-λ game produce different per-match contributions, not the same
  group-average); without them, the result is byte-identical to the current group-average behavior.
- Full suite green; real-run validation per §5.

## 8. Deliverables
Modified: `scorito/model/topscorers.py` (`build_expected_goals` signature + hand fallback), `scorito/main.py`
(`match_lams`/`avg_lam` wiring), `tests/test_topscorers.py`, finding doc. Retired: nothing. No change to
the no-ATGS path, the multiplier, market-priced matches, or scoreline/champion logic.
