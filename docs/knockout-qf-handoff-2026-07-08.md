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
