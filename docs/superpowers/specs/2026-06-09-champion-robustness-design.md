# Champion robustness recalibration — design spec

**Date:** 2026-06-09 · **Status:** approved · **Author:** R. van Bruggen + Claude

## 1. Problem
A multi-agent review found the champion recommendation (Argentina) is an over-leveraged knife-edge:
- `FIELD_SHARPNESS = 2.0` models a betting-syndicate field (~10 of 31 rivals all on Spain). At a realistic
  amateur dispersion (~1.0–1.5) the pool-win pick is **Spain**; Argentina only wins at sharpness ≥2.0,
  and `pool_win_champion` returned `stable=False` yet `main` shipped the raw argmax anyway.
- The model over-rates Argentina's outright (12% vs Polymarket ~8%) because `priors.MARKET` has no
  Argentina anchor (it falls back to Opta 10.4%, blended with a bullish sim).
- The report's champion cluster prints the 1-σ value while saying "~2 standard-errors".

A separate "goal realism" concern from the review is **dropped** — verified unnecessary: all 72 matches
carry a market total line and `goals.goals_from_odds` rescales `λ₁+λ₂` to it (sum = 2.5 confirmed), so the
grid is not goal-starved; and deliberately boosting draws via `DC_RHO` would contradict the validated
finding that scoreline draw-differentiation is ≈neutral at this pool size.

## 2. Goals / Non-goals
- Make the champion recommendation **robust** at a realistic field dispersion and reflect the money market,
  so the default becomes the high-floor pick (Spain) with the high-leverage option (Argentina/Portugal)
  shown as a deliberate, disclosed dart.
- **Non-goals (YAGNI):** no `DC_RHO`/goal-total change (verified unnecessary); no new per-team amateur-bias
  model (e.g. explicit Netherlands home-bias) — out of scope; no change to scoreline/topscorer *logic*
  (only the shared `FIELD_SHARPNESS` value moves, which is re-validated downstream).

## 3. Realistic field sharpness
`config.FIELD_SHARPNESS`: **2.0 → 1.5** (mild chalk: amateurs chase news-favourites somewhat but disperse
on feelings + home bias — not a syndicate). NOTE: `FIELD_SHARPNESS` is the *global* field-chalkiness used
by the champion field, the topscorer fame field, and `scoreline_ownership`. Lowering it makes the whole
modelled rival field less concentrated, so §7 **re-validates** the champion (→ robust Spain) AND the
topscorer engine (must still beat its EV+reserve baseline — it's safeguarded so it cannot underperform).

## 4. Realistic stability sweep
`pool.pool_win_champion(...)`: change the default `sharpnesses=(1.5, 2.0, 3.0)` → `sharpnesses=(1.0, 1.5,
2.0)` so stability is checked across *plausible* amateur dispersions, not chalk extremes. The recommendation
is still computed at `config.FIELD_SHARPNESS` (now 1.5 ∈ the sweep) via `_best_with_floor` with the
SE-aware `eps`; `stable` = argmaxes agree across the realistic sweep. No other logic change.

## 5. Market anchors
`priors.MARKET`: extend to the current Polymarket title odds (June 2026) so the blended outright stops
over-rating Argentina:
```python
MARKET = {"Spain": 0.16, "France": 0.16, "England": 0.11, "Argentina": 0.08, "Brazil": 0.08}
```
`blended_probs` already averages Opta+MARKET where both exist, so Argentina's prior drops from 0.104 →
0.092 and the blend respects the money market. (Values are genuine probabilities, intentionally not
renormalized — consistent with the existing convention.)

## 6. Report (`report.py` champion recommendation block)
- Fix the label: print **`±{2*se:.1%}`** (the cluster is built with `top − 2·se`), keeping "~2
  Monte-Carlo std-errors".
- Reframe the recommendation as **robust pick + optional dart**: `rec = result.champion[0]` (the pool-win
  argmax = the high-floor robust pick); `dart = max(result.champion, key=lambda r: r.leverage)` (the
  highest-leverage differentiation team). Text: "Robust pick: **{rec.team}** ({pool_win:.1%}, highest floor
  at a realistic field). If your pool is unusually chalk-heavy on the favourites, **{dart.team}** is the
  higher-leverage dart." Keep the host-avoidance caveat. If `dart.team == rec.team`, omit the dart clause.

## 7. Validation (real run)
Re-run `--odds-file ... --atgs-file ... --risk balanced` and confirm:
- champion default is now **Spain** (robust), with Argentina/Portugal surfaced as the leverage dart, and
  the champion table's Win-pool reflects the less-chalky field;
- the topscorer engine still selects 6 with pool-win **≥** the EV+reserve baseline at `FIELD_SHARPNESS=1.5`
  (re-run the engine-vs-baseline diagnostic; the safeguard guarantees ≥, confirm the magnitude);
- scorelines unchanged in character (still near-chalk).
Document in `docs/champion-robustness-2026-06-09.md` (before/after champion table + the field-sharpness
rationale + topscorer re-validation).

## 8. Config / error handling
- `FIELD_SHARPNESS=1.5` is a single constant; all consumers already read it. No new failure modes.
- `priors.MARKET` new keys must exist in `OPTA` for `blended_probs` averaging; Argentina/England/Brazil all
  do. (Spain/France already present.)
- The report `dart`/`rec` read existing `ChampionRec` fields (`leverage`, `team`, `pool_win`).

## 9. Testing (TDD)
- `test_priors`: `MARKET` includes Argentina/England/Brazil; `blended_probs()["Argentina"] < OPTA["Argentina"]`
  (the anchor pulls it down); `blended_probs` still averages where both exist and uses Opta otherwise.
- `test_config`: `1.0 <= FIELD_SHARPNESS <= 2.0` (realistic range; not a syndicate-chalk value).
- `test_pool`: `pool_win_champion`'s default `sharpnesses` are all `<= 2.0` (realistic dispersions only).
- Full suite green; real-run validation (§7) is the behavioral check (champion → Spain).

## 10. Deliverables
Modified: `scorito/config.py` (FIELD_SHARPNESS), `scorito/model/pool.py` (sweep default),
`scorito/data/priors.py` (MARKET), `scorito/report.py` (SE label + robust/dart text),
`tests/{test_priors,test_config,test_pool}.py`, finding doc. Retired: nothing. No change to goals/grid,
scoreline, or topscorer logic.
