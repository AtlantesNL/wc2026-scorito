# Round of 16 — handoff / runbook (2026-07-03, updated)

**Status: engine ready, data refreshed, lead-protection tilt shipped. 133 tests green.**
Tomorrow is small work: confirm tonight's winners, re-pull odds, run one command, transcribe.
Design spec: `docs/superpowers/specs/2026-07-03-r16-lead-protection-design.md`.

## Situation
- **1st place**: you 3320, #2 3244 (**+76**), #3 3119 (**+201**). Payout **graded** (1st>2nd>3rd).
- **Objective: protect the lead / win** ⇒ **mirror the chalk**, no contrarian picks. Both rivals play
  pure chalk (favourites + star ATTs, no defenders, no draws); #2 mirrors us (only Haaland vs Lautaro
  differed in R32); #3 remote (dead differential — Brobbey eliminated).
- R16 scoring: exact **135** / toto **90** (XOR, 120'); topscorers **ATT 24 / MID 48 / DEF·GK 96**,
  goals this round only, excl. shootout. Ratios identical to R32 → pick *shape* round-invariant.

## The lead-protection tilt (why the engine now self-corrects)
Pure max_ev chased high-multiplier **differentials** (Hakimi DEF ×96, Saibari MID ×48 vs weak Canada)
into the top-4 — a *chaser's* play. Fixed: for ranking, the multiplier is compressed toward the
attacker's via `shrink_mult(mult, LEAD_PROTECTION_MULT_SHRINK=0.5)` (config, per-round `lead_shrink`;
R32=1.0 no-op → byte-identical, R16=0.5). A leader mirrors the attacker-heavy field; a longshot DEF/MID
the field doesn't own only adds variance to our margin. True EV is still shown for points.
**Combined with the ATT-only brace de-bias, the engine now returns the chalk-ATT slate automatically.**

## Current predictions (from tonight's cached odds — the 6 confirmed ties are FINAL barring team news)

### 6 ready scorelines (25-book market)
| Tie | Pick | Advancer | Win% |
|---|---|---|---|
| Canada – Morocco | 0–1 | Morocco | 59% |
| Paraguay – France | 0–2 | France | 80% |
| Brazil – Norway | 1–0 | Brazil | 54% |
| Mexico – England | 0–1 | England | 43% (coin-flip, host) |
| Portugal – Spain | 0–1 | Spain | 53% (coin-flip) |
| USA – Belgium | 1–0 | USA | 37% (coin-flip, host) |

Ties #7 (Colombia–Egypt) and #8 (Switzerland–Argentina) are Elo placeholders until tonight resolves.

### Topscorers (lead-protection slate, provisional)
Current engine output: **Messi · Mbappé · Oyarzabal · Dembélé** (all ATT; diversified swaps Dembélé→Vinícius).
Messi (✍️, 25.7) is a hand estimate — his R16 tie isn't set, so no market yet, and Argentina must win
tonight. **Decision for tomorrow:** consider swapping in **Haaland** to mirror #2's likely differential
(zeroes that risk; Brazil is a tough opponent so weigh the price). Next tier ~12–13 EV:
Oyarzabal / Dembélé / Vinícius / Haaland / Lautaro.

## Data refreshed today (2026-07-03)
- **Elo** re-fetched (post-group/R32 ratings).
- **h2h + ATGS** pulled for all 6 confirmed ties (25 books; 45–46 ATGS players each). Quota: 482 left.
- **Golden boot folded in**: tally now group+R32 (Kane 4, Mbappé 6, Haaland 5, Oyarzabal 4).
- **Penalty takers verified** for all 16 teams; existing flags correct for every key player.
- **CORRECTION: Raphinha OUT** for R16 (hamstring) → `R16_INJURED_OUT`; Vinícius likely Brazil's PK.
- **+8 in-form candidates added** (Balogun, Cunha, Quiñones, Barcola, Saibari, Manzambi, Xhaka, Tielemans).

## TONIGHT (small, manual — only what tonight's 3 games decide)
Edit `scorito/data/knockout_fixtures.py`:
1. Confirm ties #7/#8 participants (expected **Colombia, Egypt, Argentina**); swap any upset (and add a
   topscorer candidate for a new team via `topscorer_candidates.py` if needed).
2. Update `STANDINGS` with the post-games points (gap should hold ~+76; up if Lautaro scored).
3. Add any R16 suspensions to `R16_INJURED_OUT`.

## TOMORROW (one command + eyeball)
```
python -m scorito.knockout --round r16 --odds-key dfa9e6f2e2088112acc30144157a5a0e --atgs --out out/ko_r16
```
(Re-pulls fresh odds/ATGS — the Argentina/Colombia/Egypt/Switzerland R16 ties will now have markets,
so Messi/Lautaro become market-priced.) Then transcribe `out/ko_r16/{report.md,picks.csv}`. Eyeball:
- the **Haaland-mirror-#2** topscorer call once his and Kane's R16 prices are in;
- **positions** of Salah / Luis Díaz in-app (ATT vs MID = multiplier lever);
- all four topscorers are **starting**; refresh `R16_INJURED_OUT` with team news.

## Known, deliberate limitations
- Form-blend results file is a manual R32 supplement (verified scorers); it's cache-only (gitignored)
  and doesn't affect ATGS-priced picks — only the ✍️ fallback + the Goals column.
- No leverage/differentiation mode: intentional. A leader mirrors; only a chaser differentiates.
