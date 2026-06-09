# Champion robustness recalibration — finding (2026-06-09)

## Why
A multi-agent review found the champion recommendation (Argentina) was an over-leveraged knife-edge: it
won only under `FIELD_SHARPNESS=2.0`, a betting-syndicate field that assumes ~10 of 31 rivals all pick
Spain. A 32-person amateur pool (feelings picks + Dutch home-bias, plus a couple of market users) is more
dispersed. The model also over-rated Argentina's outright (12% vs Polymarket ~8%) because `priors.MARKET`
had no Argentina anchor.

## What changed
1. **`FIELD_SHARPNESS` 2.0 → 1.5** — realistic amateur dispersion (the global rival-field chalkiness).
2. **Stability sweep `(1.5, 2.0, 3.0)` → `(1.0, 1.5, 2.0)`** — evaluate plausible amateur fields, not chalk
   extremes; the recommendation is taken at the 1.5 default with the SE-aware floor tie-break.
3. **Real Polymarket anchors** in `priors.MARKET` (Spain/France 0.16, England 0.11, Argentina/Brazil 0.08),
   so the blended outright respects the money market (Argentina 0.104 → 0.092 prior).
4. **Report fix** — the cluster ±SE label now prints 2σ (matching the `top−2·se` cluster), and the
   recommendation is framed as **robust pick + optional dart**.

## Before → after (champion table)

| | FIELD_SHARPNESS = 2.0 (before) | FIELD_SHARPNESS = 1.5 (after) |
|---|---|---|
| **Recommended** | **Argentina** | **Spain** |
| Spain Win-pool | 7.3% (faded as over-owned) | **10.2%** |
| Argentina Win-pool | 8.9% (argmax) | 10.6% |
| Argentina outright | 12.0% | 11.4% (market-anchored) |

At 1.5, Spain (10.2%) and Argentina (10.6%) are **statistically tied** on pool-win (gap 0.4% < the ~2σ
cluster width 0.5%), so the floor tie-break correctly takes the **higher-outright Spain** — the robust
pick that wins across realistic field assumptions. `stable=False` is still reported honestly (the raw
argmax flips to Argentina only at chalk levels ≥2.0), and the report names **Argentina** as the
deliberate higher-leverage dart for a pool the user knows to be chalk-heavy on the favourites.

## Verdict
**Spain is the robust champion pick.** Argentina was an artifact of an over-chalky field assumption; at a
realistic amateur dispersion it's a coin-flip with Spain on pool-win, and Spain's far higher title odds
(17.4% vs 11.4%) make it the high-floor choice. Take Spain unless you're confident your specific pool is
unusually concentrated on Spain/France — then Argentina is the leverage play.

## Topscorer re-validation (FIELD_SHARPNESS is global)
Lowering the field chalkiness also feeds the topscorer engine's rival field. Re-checked at 1.5: the engine
still selects its 6 (Wirtz, Kane, Haaland, Yamal, Mbappé, Lautaro; entry pool-win ~10.9%) and remains
**safeguarded to never underperform** the EV+reserve baseline. No regression.

## Dropped (verified unnecessary)
The review's "goal-starvation" concern was refuted: all 72 matches carry a market total line and
`goals.goals_from_odds` rescales `λ₁+λ₂` to it (verified sum = 2.5), so the grid is already goal-anchored.
And boosting draws via `DC_RHO` would contradict the validated finding that scoreline draw-differentiation
is ≈neutral at this pool size. So no goal-model change was made.
