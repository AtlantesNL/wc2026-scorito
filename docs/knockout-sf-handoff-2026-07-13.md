# Semifinals — QF retro + SF runbook (2026-07-13)

**Deadline: tomorrow Tue 2026-07-14 21:00 CEST — SF1 France–Spain kicks off 15:00 ET Dallas.**
All QF results below cross-verified against ≥2 independent sources per tie (ESPN/FOX/Al Jazeera/
AP/England FA/Yahoo; FIFA.com match centre is JS-rendered and unusable; the usual Wikipedia
caveat stands).

## QF retro — banked 512 vs 407 expected (+26%), reconciles EXACTLY (4119 → 4631 in-app)

| # | Tie | Pick | Actual (120') | Outcome | Pts |
|---|---|---|---|---|---|
| 1 | France – Morocco | 1-0 Fra | **2-0** (Mbappé 60', Dembélé 66'; Mbappé pen SAVED 28') | toto | 120 |
| 2 | Spain – Belgium | 1-0 Esp | **2-1** (F. Ruiz 30', CDK 41', Merino 88') | toto | 120 |
| 3 | Norway – England | 0-1 Eng | **1-2** aet (Schjelderup 36'; Bellingham 45+2', 93') | toto | 120 |
| 4 | Argentina – Switzerland | 1-0 Arg | **3-1** aet (Mac Allister 10', Ndoye 67', Álvarez 112', Lautaro 120+1') | toto | 120 |

Topscorers (×32 ATT): **Mbappé 1 +32 · Kane 0 · Messi 0 (assist; 9-game streak ends) ·
Haaland ⚑ 0 (subbed 106', 14-match Norway streak ends)** = 32 vs 86.0 EV. Match points 480 vs
320.8 EV. Total 512 = the unique decomposition (480 must be 4 totos or 2 exacts+toto+zero;
32 = exactly one ATT goal) — the four-toto reading is source-confirmed.

### Model vs expectation (lock-day cached-odds replay)
- Exacts 0 vs 0.51 expected · totos 4 vs ~1.9 · zeros 0 vs ~1.6 → +50% over match EV. Third
  straight round of overshoot (R32 +40%, R16 +31%, QF +50%) — all three were chalk-friendly
  rounds; this is favourable variance, NOT a systematic edge. Do not start expecting it.
- Advancers **4/4** vs ~2.42 expected; Brier on P(advance) ≈ **0.158** (R16 0.186, coin-flip
  0.25). The 53% Nor–Eng coin-flip — the round's flagged residual risk — landed our side.
- Total goals 12 vs 10.0 expected (2-3 per tie modelled at 2.5) — every favourite won by MORE
  than the modal 1-0/0-1, hence 4 totos and 0 exacts. Same mild-over pattern as R16 (23 vs 21.6).
- Topscorers ran −63% (1 goal vs 2.69 expected from the four picks). P(≤1 | Poisson 2.69) ≈ .25 —
  underwhelming but not diagnostic on its own; see the margin retest below for the real signal.

### The slot-4 mirror (Haaland ⚑, forced) — verdict: cost ZERO, worked as designed
Haaland 0 and the free-ranking alternative Oyarzabal 0 (subbed 79') — the −1.0 EV paid for the
insurance was refunded by both blanking. The mirror did its job: whatever #2 held at slot-4,
Haaland could not become a differential against us. The miss everyone (us, and any rival not
holding him) shared: **Bellingham braced again** (MID, our #7 at 17.6 EV) — +128 for anyone who
held him. That is the chaser's play our lead-protection shrink deliberately refuses; it stays
correct while we lead. NOTE for SF: Bellingham (6 goals, MID ×80 in the SF) is now the likely
slot-4 battleground — read rivals' slates in-app before deciding (see runbook step 1).

### Rival provenance — arithmetically PROVEN shuffled this round
Post-QF board: you **4631** · #2 neemaar jr **4475** (+156) · #3 thomneleman **4337** (+294).
Any entrant's QF delta must be 60s + 32t (s,t ≥ 0) ⇒ ≡ 0 (mod 4). From the in-app-verified R16
totals: 4475−4001 = 474 ≡ 2 (mod 4) — impossible; 4337−3860 = 477 odd — impossible. So **today's
#2/#3 are NOT last round's #2/#3** (both climbed from below 2nd/3rd). The 2026-07-10 provenance
rule (rank ≠ identity across rounds) is no longer just a caution — it provably bit this round.
Consequence: we know NOTHING about the current rivals' topscorer tendencies until their SF (and
ideally QF) slates are read in-app. Lead moved +118 → +156 on #2, +259 → +294 on #3.

## Method findings closed this session (2026-07-13)

### 1. Price-implied totals — REFUTED, TODO closed, keep line-snap
Replayed both cached QF snapshots (Jul-8 + Jul-9 lock) through the full pipeline (Shin 1X2 →
goal_expectancy → λ rescale) with the λ-sum set to the price-implied total (devigged P(over 2.5)
solved through a Poisson total; proportional AND Shin devig of the 2-way O/U tested — identical
to 3 decimals). Result: implied totals 2.38–2.90 (matches the Jul-8 review's 2.41–2.89), max
λ_fav **1.94 < 2.0** on every tie/snapshot/method ⇒ **price-implied flips ZERO QF picks**. The
Jul-8 review's materiality claim ("would flip 3 of 4 pick digits, ~+3.7 EV") contradicted its own
confirmed threshold ("2-0 needs λ_fav ≳ 2.0, max observed 1.94") and does not reproduce —
treat that sentence in `knockout-qf-handoff-2026-07-08.md` as CORRECTED here. Scoreboard: R16
backtest line-snap 585 vs price-implied 540; QF identical picks ⇒ tie. Line-snap has never been
beaten. **Decision: keep line-snap for the SF; drop the A/B from the TODO list.**

### 2. ATGS flat-margin de-vig — inflation CONFIRMED on the doubled sample, now quantified
Band test, QF lock ATGS (172 priced players, 4 events) vs realized scorers (all 11 matched
under `_norm`):

| implied p band | n | implied avg | realized | gap |
|---|---|---|---|---|
| ≥ .50 | 3 | .513 | .333 | −35% (n=3 — noise; Mbappé the 1) |
| .35–.50 | 8 | .396 | .125 | **−68%** |
| .20–.35 | 35 | .252 | .114 | **−55%** |
| .10–.20 | 51 | .141 | .098 | −30% |
| < .10 | 75 | .073 | .000 | −100% |

Σ implied ≈ 26.2 "scorers"; 11 realized. The market's ATGS overround is ~2×, concentrated in
the mid/tail, and the flat `ATGS_MARGIN=1.06` removes 6% of it. Direction and shape replicate
the R16 finding (mid-band ~40% low) — two independent rounds, same signature. Still
ranking-safe *within* a match (monotone), but **price-dependent inflation biases cross-position
and cross-match near-ties toward the longer-priced player** — exactly the shape of the likely
SF slot-4 call (Bellingham MID ~.25-band vs an ATT head-band alternative). **SF action (small,
principled): per-event renormalisation — scale each event's implied p's so Σp = E[distinct
scorers | match λ] (≈ 0.9·λ_total; QF check: predicts ~9.2 vs 11 realized, vs flat-margin's 26).**
If not shipped in time, at minimum distrust the EV column below the head band and hand-check any
cross-position near-tie at slot-4.

### 3. Pinnacle ATGS triple-listing — dedupe still open (odds.py:136)
Unchanged from lock-day: median per (book, player) first, then median across books. Small,
tested, do it before the SF pull.

## Standings + SF bracket (all agent-verified Jul-12/13 sources)

| SF | Tie | Date | Venue | Notes |
|---|---|---|---|---|
| 1 | **France – Spain** | Tue 14 Jul, 21:00 CEST | Arlington/Dallas | Tchouaméni MAJOR doubt (thigh); Mbappé minor ankle knock, "completely fine"; Pino fit, Nico Williams fit-but-XI-doubt |
| 2 | **England – Argentina** | Wed 15 Jul, 21:00 CEST | Atlanta | Quansah SUSPENDED (2-game ban, misses SF); Rice questionable (sickness + back, off at HT); Konsa knock; Medina (ARG) OUT calf; Messi eye cut, available |

Third place Sat 18 Jul Miami; **Final Sun 19 Jul East Rutherford**. Yellow slates WIPED after the
QF (confirmed: no accumulation suspensions — Bellingham/Rice/etc. all clean); only Quansah misses
the SF. Golden Boot after QF (Goal.com + Yahoo agree line-for-line): **Mbappé 8 (3 assists —
tiebreak lead) · Messi 8 · Haaland 7 (elim.) · Bellingham 6 · Kane 6 · Dembélé 5 · Oyarzabal 4**;
Álvarez 1 (QF winner was his first), Lautaro 2.

## TOMORROW (lock day, Tue 2026-07-14, lock 21:00 CEST) — in order
1. **In-app**: real standings + BOTH rivals' entered SF slates (slot-4 especially: Bellingham?).
   Rank-shuffle proof above means prior rounds' reads do NOT transfer — fresh reads only. Update
   `STANDINGS` in `knockout_fixtures.py`.
2. **Confirm SF scoring in Spelregels** — pattern says exact 225 / toto 150, topscorer ATT 40 /
   MID 80 / DEF·GK 160 (5× group), 4 slots, XOR, 120' — CONFIRM before coding.
3. **Extend the engine**: `KO_ROUND_SCORING["Semifinal"]` (form_games=6, brace_credit ATT-only,
   lead_shrink 0.5) + `SF_TIES` bundle + `_round_tag` "semifinal"→"sf" + `--round sf` choice.
   Regenerate r32/r16/qf to prove pick-identity. Tests.
4. **Ship the two ATGS fixes**: (a) Pinnacle (book, player) dedupe; (b) per-event Σp
   renormalisation (finding 2). Both before the odds pull; add tests + a regen-identity check.
5. **Candidate curation**: goals now Mbappé 8 · Messi 8 · Bellingham 6 · Kane 6 · Dembélé 5 ·
   Oyarzabal 4 · Álvarez 1 · Lautaro 2 (update tallies/`wc2026_scorers.json`); injured/out:
   Quansah (susp.), Medina; doubtful: Tchouaméni, Rice, Konsa; start_probs to re-check: Álvarez vs
   Lautaro (both scored), Dembélé, Oyarzabal false-9, Nico Williams bench, Rice HT-pull.
6. **Pull odds + ATGS** (`--round sf --odds-key … --atgs`; snapshot the raws). Tripwire: any
   top-10 candidate showing ✍️ in a priced event = alias miss.
7. **The slot-4 call**: everyone shares Mbappé/Messi/Kane. Slot 4 is the round's only topscorer
   differential — candidates Bellingham (MID, 6 goals, braced twice in KOs, ×80 but shrink-ranked
   at √(40·80)≈56.6) vs Dembélé/Oyarzabal/Álvarez (ATT ×40). Mirror-first: if a rival's slate is
   visible and holds one of these, weigh the QF-style forced mirror (precedent: R16 regret −48,
   QF mirror cost 0). If nothing is visible, take the engine's ranking — do NOT hand-override
   toward Bellingham just because he braced; that's outcome-chasing the shrink exists to prevent.
8. Transcribe `out/ko_sf/{report.md,picks.csv}` before 21:00 CEST. FRA–ESP lineups ~20:00 CEST —
   only a shock Mbappé/Messi-class absence reopens picks.

## PREP DONE 2026-07-13 (evening session, user go-ahead + key) — runbook steps 2-6 executed early

- **Scoring CONFIRMED in-app** (user screenshot): exact 225 / toto 150, ATT 40 / MID 80 / DEF·GK
  160 — the predicted 5× pattern exactly. Coded as `KO_ROUND_SCORING["Semifinal"]` (form_games=6).
- **Engine extended** (TDD, 157 tests green, was 144): `--round sf` + SF fixtures bundle +
  `_round_tag`; STANDINGS → 4631/4475/4337 with the shuffle warning inline.
- **Both ATGS fixes shipped**: (a) Pinnacle per-(book,player) dedupe in `parse_atgs` — on the QF
  raws it moved 18 medians, zero picks; (b) **power tail de-vig** (`atgs_tail_devig`, SF-onward
  flag): per event solve k≥1 with Σpᵢᵏ = 0.9·λ_total. Live SF markets carry Σp ≈ 6.3-6.8 implied
  scorers vs target 2.45 (~2.6× overround, as the QF band test predicted); head keeps ~61% of
  implied, tail ~44%. **A/B flat-vs-devig on the live pull: top-4 IDENTICAL** — it fixes the EV
  column, not the picks. Earlier rounds keep the flat margin (replay identity).
- **Replay date-cutoff fix** (found during regen): the results file accumulates per-round scorer
  supplements, so past-round replays now pass the round's first tie date as a cutoff — without it
  the QF supplement's future goals flipped the R32 slot-4 blend. r16 + qf replays: pick-identical.
  (The r32 picks.csv-vs-report mismatch turned out to PRE-DATE today: the shipped report.md
  (Jun-28 20:30, Bellingham #4) and picks.csv (21:07, Lautaro) disagree with each other — the csv
  reflects the documented lock-night hand-evolution. Today's regen reproduces the report exactly.)
- **Candidates curated** (+24 across the four SF squads, consensus-XI start probs; positions for
  new wingers are ATT guesses ⚠️ verify in-app if one nears the slate). NB **Foden & Palmer are
  NOT in England's 26** (cut in May). QF scorer supplement added (12 goals, zero pens — Mbappé's
  28' pen was saved). Non-pen tallies now: Messi 8 · Mbappé 7 · Bellingham 6 · Kane 4.
- **Live pull DONE ~08:34 UTC Jul-13** (key live, 2/2 priced + 46/44 ATGS players; cached as
  `data/cache/{odds,atgs}_sf_raw.json`). **PROVISIONAL SLATE (out/ko_sf): Fra 1-0 Esp · Eng 1-0
  Arg + Mbappé / Kane / Messi / Oyarzabal** (EV 182; both ties market coin-flips 44%/40% with ~20%
  recorded-draw risk). Bellingham ranks #5 (sel-ranked below Oyarzabal by the chalk-mirror shrink;
  his raw EV 8.3 vs Oyarzabal 6.4 — the slot-4 tension to resolve against rival slates).
- **Remaining for lock day (Tue Jul-14, before 21:00 CEST)**: runbook steps 1 (in-app standings +
  BOTH rival SF slates → set `SF_TOPSCORER_FORCED` if mirroring), 6-re-pull (fresh odds
  cents-check ~19:00 CEST), 7 (slot-4 final call), 8 (transcribe). FRA-ESP lineups ~20:00 CEST.

## Open items beyond the SF
- 90'-settlement gap (−7-8% on market λs) and supersub appearance credit — documented, unpriced,
  still ranking-safe; revisit only if a Final-round pick is a genuine near-tie.
- R32 backtest of price-implied totals — moot after the refutation unless someone re-opens it.
