# Topscorer-ownership calibration — finding (2026-06-09)

## What we tested
The pool owner reports rivals pick topscorers "mostly famous strikers + a flier" — a partial fame bias.
We model the field's topscorer ownership as **fame-weighted** (`fame_score` = expected goals × team
factor, *dropping* the 4× position multiplier), so famous attackers get over-owned and high-multiplier
DEF/GK under-owned. We then select our 6 with `pool.pool_win_topscorers` — a greedy + coordinate-ascent
search that maximizes P(finishing 1st) through the pool-win engine — and compared it to the EV+reserve
`pick_topscorers` baseline on identical worlds/field, champion fixed.

## Result — a real (modest) edge, **champion-dependent**

At the champion the model actually ships (**Argentina**, the pool-win/leverage pick), 6000 worlds, three
independent seeds:

| seed | baseline P(win) | engine P(win) | delta | ~SE |
|------|-----------------|---------------|-------|-----|
| 1 | 0.0833 | 0.0868 | **+0.0035** | 0.0036 |
| 2 | 0.0712 | 0.0763 | **+0.0052** | 0.0033 |
| 3 | 0.0795 | 0.0858 | **+0.0063** | 0.0035 |

Consistently positive across all three independent seeds (combined ≈2.5 SE) → a **real ~+0.5pp pool-win
gain (~6% relative)**. The engine keeps the elite strikers (they're the highest-EV picks *and* your
floor) but swaps the baseline's weak second defender (Van Dijk) for a high-scoring 16× midfielder
(Bellingham) + Raphinha — the joint-portfolio call a fixed "reserve 2 defenders" heuristic can't make.

**Shipped pick (Argentina champion):** Kane, Hakimi (DEF), Mbappé, Haaland, Bellingham (MID), Raphinha.
**EV+reserve baseline:** Kane, Mbappé, Haaland, Lautaro, Hakimi, Van Dijk.

## Why champion-dependent (and the safeguard)
An earlier probe at champion = **Spain** (the over-owned title favourite the whole field also banks)
showed the greedy search getting **stuck below the baseline** (0.0608 vs 0.0622) — the differentiation
has less room when you're already on the crowd's champion. Two fixes:
1. `pool_win_topscorers` now evaluates the EV+reserve baseline too and keeps it unless the search
   *strictly* beats it — so the engine **can never ship worse than the baseline**, at any champion.
2. We only run the engine for **balanced/aggressive** risk; `max_ev` keeps pure-EV `pick_topscorers`.

## Conclusion
Unlike scoreline draw-differentiation (which validated as ≈neutral, see
`docs/scoreline-calibration-2026-06-09.md`), **topscorer ownership is a small but real lever** at a
32-person pool: 6 concentrated, high-variance, 4×-multiplier picks against a fame-biased field give the
engine room to separate. Shipped on the main path, safeguarded to never underperform EV+reserve.

## Caveats
- The edge (~0.5pp) is real but small; it's largest with a leverage champion and shrinks toward zero on
  the crowd's favourite. 6000 worlds → per-seed SE ~0.0035, hence the three-seed replication.
- Depends on the fame-bias assumption (rivals ignore the multiplier). If your pool actually games the
  32/16/8 scoring, set `--risk max_ev` to fall back to pure EV.
