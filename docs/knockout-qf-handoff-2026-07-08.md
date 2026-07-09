# Quarterfinals — R16 retro + QF runbook (2026-07-08)

**Deadline: tomorrow Thu 2026-07-09 22:00 (CEST) — first QF kicks off 16:00 ET Boston.**
All R16 results below are cross-verified against ≥2 independent sources (ESPN/FOX/FIFA/CBS/
Al Jazeera). ⚠️ The raw Wikipedia knockout-stage page fetch returned garbled winner cells again
(three mutually contradicting extractions) — never bracket-source it alone.

## R16 retro — banked 633 vs 515 expected (+23%)

| # | Tie | Pick | Actual (120') | Outcome | Pts |
|---|---|---|---|---|---|
| 1 | Canada – Morocco | 0-1 Mor | **0-3** | toto | 90 |
| 2 | Paraguay – France | 0-2 Fra | **0-1** (Mbappé pen) | toto | 90 |
| 3 | Brazil – Norway | 1-0 Bra | **1-2** (Haaland 2) | zero | 0 |
| 4 | Mexico – England | 0-1 Eng | **2-3** | toto | 90 |
| 5 | Portugal – Spain | 0-1 Esp | **0-1** (Merino 90+1') | **EXACT** | **135** |
| 6 | USA – Belgium | 0-1 Bel | **1-4** | toto | 90 |
| 7 | Argentina – Egypt | 2-0 Arg | **3-2** in 90' | toto | 90 |
| 8 | Switzerland – Colombia | 0-1 Col | **0-0** aet (SUI 4-3 p) | zero | 0 |

Topscorers (×24 ATT): **Mbappé 1 (pen) +24 · Messi 1 +24 · Oyarzabal 0 · Lautaro 0 (bench, on 66')**
= 48 vs 67.9 EV. Match points 585 vs 447 EV.

### Model vs expectation (lock-day cached-odds replay, byte-identical EVs)
- Exacts 1 vs 0.97 expected · totos 5 vs 3.50 · zeros 2 vs 3.52 → ran ~+31% over match EV
  (R32 ran ~+40%; two straight rounds over — good, but n is small and both had chalk-friendly
  outcomes; do NOT start expecting overshoot).
- Advancers 6/8 vs ~5.4 expected; Brier on P(advance) ≈ **0.186** vs 0.25 coin-flip baseline.
  The two misses were the model's own coin-flips (Brazil 55%, Colombia 47%); its two *least*
  confident picks (England 43%, Belgium 38%) both hit. No calibration red flag.
- Total goals: 23 actual vs ~21.6 expected across the 8 ties — mild under, within noise.
- Process wins: (a) the lock-day **USA→Belgium flip** on the 2-cent odds move was worth +90
  (USA lost 1-4); (b) the lock-day **bracket cross-pairing catch** (Arg-EGY / Sui-COL) saved two
  ties' worth of picks; (c) hand-priced Messi/Lautaro were confirmed by the late market.
- **The one regret — we didn't mirror Haaland.** Our own strategy memo said "hand them no
  topscorer differential"; the slate still handed #2 their Haaland slot (his 12.0 EV ranked just
  below Oyarzabal 13.3 / Lautaro 13.1). He braced: −48 swing vs #2 for ~1 EV saved. The
  lead-shrink tilt fixed the *position-multiplier* chase but has no concept of *rival-mirroring*.
  For the QF this is THE live decision again — Haaland is alive (vs England) and #2 likely still
  holds him.

## Standings entering the QF (projected — VERIFY IN-APP)
You **4119** (3486 + 633). #2 ≈ **4085 (+34)** if they full-mirrored scorelines and played the
Kane/Haaland slate; #3 ≈ 3900 (+219). The +106 cushion has most likely shrunk to a few dozen
points — **read the real leaderboard + both rivals' R16/QF slates in-app before any pick call.**

## QF bracket (verified: Wikipedia bracket + ESPN + FOX + Al Jazeera agree)
| QF | Tie | Date | Notes |
|---|---|---|---|
| 1 | **France – Morocco** | Thu 9 Jul, Boston | Tchouaméni OUT; Saibari doubtful (hamstring, MRI) |
| 2 | **Spain – Belgium** | Fri 10 Jul, LA | Nico Williams doubtful; Onana OUT (ACL); KDB/Lukaku/CDK in form |
| 3 | **Norway – England** | Sat 11 Jul, Miami | Haaland 7 goals; Quansah suspended (red); NOR camp illness |
| 4 | **Argentina – Switzerland** | Sat 11 Jul, KC | Messi 8 (Boot lead); SUI 0 conceded in 120' in KOs |

Semis: QF1w–QF2w (Jul-14 Dallas) · QF3w–QF4w (Jul-15 Atlanta). Golden Boot: Messi 8, Mbappé 7
(2 assists), Haaland 7, Kane 6. Cards wiped at KO start, next wipe AFTER the QF → a QF yellow =
semi ban (Hakimi, Rice, Bellingham, Xhaka each one booking away) but only Quansah misses the QF.

## TOMORROW (lock day) — in order
1. **In-app**: real standings + rivals' entered QF slates (does #2 still hold Haaland?). Update
   `STANDINGS` in `knockout_fixtures.py`.
2. **Confirm QF scoring in Spelregels** — pattern says exact 180 / toto 120, topscorer ATT 32 /
   MID 64 / DEF·GK 128 (4× group), but CONFIRM in-app before coding.
3. **Extend the engine**: `KO_ROUND_SCORING["Quarterfinal"]` (form_games=5, brace_credit ATT-only,
   lead_shrink 0.5) + `--round qf` wiring to the QF fixtures bundle. Regenerate R32+R16 to prove
   byte-identity. Tests.
4. **Candidate curation (required)**: pool has NO De Ketelaere (2 vs USA), Lukaku, Ounahi (2),
   Rahimi, Merino, Vanaken, Enzo Fernández — add with team news; re-check Saibari/Manzambi/
   Nico Williams/Strand Larsen fitness; Lautaro was BENCHED in R16 (Alvarez started) → start_probs.
5. **Pull odds + ATGS** (`--round qf --odds-key … --atgs`, ~450 credits left). Tripwire: any
   top-10 candidate showing ✍️ in a priced event = alias miss.
6. **The Haaland call**: if the lead is thin and #2 holds Haaland, mirroring him (and generally
   full-mirroring #2's slate) is the variance-minimising play — codify or decide explicitly this
   time; don't leave it as an eyeball note again.
7. Transcribe `out/ko_qf/{report.md,picks.csv}` before 22:00 CEST.

## LOCK DAY 2026-07-09 — executed (~19:00-19:45 CEST, lock 22:00)

**FINAL SLATE (out/ko_qf, regenerated from the Jul-9 19:15 CEST odds pull): Fra 1-0 · Esp 1-0 ·
Nor 0-1 Eng · Arg 1-0 + Kane / Mbappé / Messi / Haaland ⚑ (forced).** Model EV 405.

- **Fresh odds+ATGS pulled** (key live, 4/4 priced; Jul-8 snapshots backed up as
  `data/cache/*_qf_raw_0708.json`). Diff vs Jul-8: cents-level only (Norway 4.15→4.20,
  Spain 1.62→1.65, ATGS medians flat — Haaland 2.30→2.30, Oyarzabal 2.20→2.20). NOT material.
- **The free ranking flipped slot-4 to Oyarzabal** (17.9 vs Haaland 16.9; Jul-8 gap was 0.5, now
  1.0 — drift on a near-tie, not a signal). Decision held: **Haaland, now CODIFIED** as
  `QF_TOPSCORER_FORCED` + `forced_topscorers=` in `run_knockout` (raises if the name drops out of
  the candidate pool; ⚑ in report). 5 new tests, 144 green. r32/r16 regen verified pick-identical.
- **Four-agent news sweep (one per tie, all Jul-9 sources):** Saibari coach-CONFIRMED OUT (Rahimi
  starts); Norway flu RESOLVED (team doctor: all healthy; Haaland never affected, trained Jul-9);
  Oyarzabal confirmed false-9 + pen #1; Nico Williams available-but-bench (Baena); KDB recalled,
  Lukaku bench everywhere; Messi fine, full ARG squad available; Álvarez consensus starter
  (Lautaro 0.50→0.45, Álvarez 0.75→0.80); Manzambi leans out (kept out); Xhaka available.
  Zero pick impact — the sweep de-risked the slate rather than changed it.
- **Data artifact logged (SF TODO in `odds.py`):** Pinnacle triple-lists players within one
  event's ATGS market (Haaland 2.2/2.33/1.62) → one book gets 3 of ~6 pooled-median votes
  (Haaland 2.30→2.25, ~1% P). Ranking-safe, not hot-fixed on lock eve; dedupe per (book, player)
  before the semis.
- **Left for the user (in-app, before 22:00 CEST):** transcribe the 8 rows above; glance at #2's
  QF slate if visible (Haaland repick confirms the mirror; nothing changes either way — the call
  is locked); FRA-MAR official lineups drop ~21:00 CEST — only a shock Mbappé absence would
  warrant a rethink of tie 1.

## Scoreline-reasoning review (2026-07-08 late — inline + independent fork, verdicts agree)

User asked why all four QF picks are 1-0/0-1. Full adversarial verification of the explanation:
- **CONFIRMED**: XOR EV = 60·P(exact)+120·P(side) (code-exact); within-side ranking = cell prob;
  P(2-0)/P(1-0) = λ_fav/2 (DC ρ=.001 negligible) → 2-0 needs λ_fav ≳ 2.0 and no QF favourite
  clears it (max 1.94); table numbers reproduced from scratch; R16's 0-2/2-0 picks had λ 2.25/2.08;
  side term = 90-91% of pick EV.
- **CORRECTED**: recorded-draw risk is **21-24%** per tie (was misstated 15-19%; draw picks still
  EV 31-36 vs 70-86, nowhere near). And "market prices all ties at ~2.7" was an artifact: every tie's
  **median totals LINE is the standard 2.5** and `goals_from_odds` snaps the λ-sum to the line,
  discarding the over/under PRICES where tempo opinion lives (devigged P(over 2.5): Fra-Mar .48,
  Esp-Bel .53, Nor-Eng .55, Arg-Sui .43 → price-implied totals 2.41-2.89, NOT uniform).
- **Materiality**: price-implied totals would flip 3 of 4 QF pick DIGITS (1-0→2-0 ×2, 0-1→1-2;
  sides never change), ~+3.7 EV on paper. **But the R16 backtest (n=8, actual results) scored
  line-snap 585 vs price-implied 540** — the higher-total variant loses the Portugal 0-1 exact.
- **DECISION: keep line-snap for the QF** (unvalidated ~1% EV tweak on lock eve; near-tie digits
  should lean to the field's chalk digits anyway — leader mirrors). **SF-round TODO: evaluate
  price-implied totals properly** (add R32 backtest, Shin-devig the O/U, then A/B the two slates
  across all scored KO rounds before adopting).

## Topscorer-method review (2026-07-08 late — two adversarial forks: code semantics + empirical)

User asked whether the goalscorer picking is done "the right way". Verdicts (both forks agree):
- **NO BUG affects any current or plausible pick.** Double-count audit clean (pens + team factor
  market-path-only-excluded, non-pen blend vs pen_share disjoint, appear-vs-start asymmetry sound);
  brace/shrink math exact (`(p1+credit·extra)·mult`, shrink {32,64,128}→{32,45.25,64}, ko_sel ranks /
  ko_ev displays); orientation/alias/price-guard edge cases hold; QF composition correct.
- **Head calibration GOOD** (the region picks come from): R16 top-8 ATTs 4.82 expected goals →
  5 realized; both p≥.5 players scored; consistent with the R32 backtest (8.1 vs 9).
- **Tail/mid-band INFLATED**: flat `ATGS_MARGIN=1.06` vs a real 40-60% longshot-concentrated
  overround; implied p in the .2-.5 band realized ~40% low (z≈2.3, one round). Ranking-safe
  (monotone); EV column untrustworthy above ~price 6. Re-test after the QF (sample doubles) before
  any margin retune. (Comments added in `topscorers.py`.)
- **De-bias rationale CORRECTED**: tournament-wide braces fit Poisson at EVERY position (ATT 37%
  vs 23-31% implied, MID 18% vs 14% — Bellingham & Ounahi braced in R16 alone). "Raw Poisson
  inflates MID braces" was the margin problem in disguise. The ATT-only brace credit stays as
  deliberate chalk-mirroring (cost so far: zero — every R16 ranking variant realized the same 48).
- **Variant A/B on R16**: base vs full-Poisson vs no-brace vs no-shrink vs no-appear → all realized
  48 (contested slot-3/4 candidates all blanked). n=8 cannot discriminate these knobs; they are
  strategy choices, and the shipped slate was weakly-best.
- **Minor level biases (ranking-safe, documented in code, no action)**: 90'-settlement gap ≈ −7-8%
  on all market λs; supersub appearance underrated (Lukaku EV 5.0 → ~8.2 at true P(appear)).
- **Data nit RESOLVED (2026-07-08, 3 sources: ESPN/Al Jazeera/FOX)**: the R32 Cape Verde goal was
  **Lisandro** Martínez (92') — the supplement was correct; the "Lautaro" claim in one news-agent
  report was wrong. Full goal-tally audit vs Goal.com golden-boot standings: all 7 leaders
  reconcile exactly under `_norm` (Messi 8 · Mbappé 7/6np · Haaland 7 · Kane 6/4np · Dembélé 4 ·
  Oyarzabal 4 · Bellingham 4); Lautaro correctly stands at 1 (group pen), 0 non-pen.
