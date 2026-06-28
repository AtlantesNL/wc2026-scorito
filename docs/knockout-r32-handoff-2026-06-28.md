# Scorito WC2026 — Round-of-32 Handoff (2026-06-28)

**Purpose:** complete continuation state so a fresh session can resume cold and finish before the
lock. Group stage is over; this is the **first knockout phase (Round of 32)**. Everything we
researched and decided this session is captured below — do **not** re-run the web-research agents
(it would burn tokens/credits); the findings are here.

---

## 0. Situation & deadline (READ FIRST)

- **Standing:** we are **1st** in a **~30-person pool**, **2536 pts** vs #2 on **2516** (lead = **20**).
- **Payout:** pool pays **top-3** → posture is **`max_ev` (protect the lead, pure EV, near-chalk).** User confirmed this.
- **Rounds left:** R32 → R16 → QF → SF → final (5 more lock events). A 20-pt lead is thin; play reliable EV.
- **LOCK: tonight 21:00 CET = first R32 kickoff (South Africa–Canada).** All R32 picks lock at once.
- **What must be submitted tonight:** **16 R32 match predictions** (scoreline + advancer) **+ 4 topscorers.**
- **Champion pick is NOT in play** — it was a one-time season pick (Spain, locked, and Spain *advanced*, so still live). No champion work needed.

---

## 1. Confirmed Scorito knockout rules (from user's in-app Spelregels paste — AUTHORITATIVE)

**Match prediction — "stand na max. 120 minuten":** you predict the result *after extra time*
(ET goals count; the penalty **shootout does not** change the recorded score, so a tie decided on
pens is recorded as the 120-min draw). XOR scoring (NOT additive):

| Outcome | Points |
|---|---|
| **Resultaat correct** (exact score) | **90** |
| **Toto correct** (right 1/X/2 only) | **60** |
| Wrong | 0 |

→ Same XOR shape as the group phase, **doubled** (group was 45/30). Exact pays 90, **not** 90+60.
You also **nominate the advancer** (matters mainly when you predict a draw → who wins on pens).
*Open item to confirm in-app:* whether the advancer carries separate points — it does **not** change
a `max_ev` pick (we back the favourite either way).

**Topscorers — "Selecteer 4 topscorers":** pick **4**; goals **this round only** (per-round, NOT
cumulative — new picks each round); **excludes shootout** goals (in-play + ET penalties count).
Multipliers (doubled vs group, same 4:2:1 ratio):

| Pos | Points per goal |
|---|---|
| Aanvaller (ATT) | **16** |
| Middenvelder (MID) | **32** |
| Verdediger (DEF) | **64** |
| Keeper (GK) | **64** |

**Key consequence:** every alive team plays exactly **one** R32 game, so a topscorer pick =
`multiplier × P(start) × E[goals vs that one specific opponent]`. Driven entirely by the matchup.
The group-phase "under-owned defender" logic was a *leverage* play; under `max_ev` the 4:2:1 ratio
rarely beats a top forward's ~0.6 single-game xG, so expect mostly **penalty-taking forwards / high-xG
mids on the strongest favourites vs the weakest/leakiest defences**. The 2× MID multiplier (32) makes
**Bellingham / De Bruyne** genuine dark horses (a mid needs only ~half a striker's goal prob to match EV).

---

## 2. The bracket — 32 qualified teams + 16 R32 fixtures (verified across Wikipedia/Sky/ESPN/NBC/Yahoo)

**All 7 pre-tournament favourites advanced** (Spain, France, Argentina, Brazil, Germany, England won
groups; Portugal runner-up K, Netherlands won F). **Notable eliminations: Iran & Uruguay** (3rd-place
casualties); also out: Scotland, South Korea, Qatar, Haiti, Türkiye, Czechia.

**R32 fixtures (favourite-first labelling is the bracket's, NOT always the betting favourite — see §3):**

| # | Tie | Date | Venue |
|---|---|---|---|
| 1 | South Africa vs Canada | Sun Jun 28, 12:00 PT | SoFi, LA |
| 2 | Brazil vs Japan | Mon Jun 29, 12:00 CT | NRG, Houston |
| 3 | Germany vs Paraguay | Mon Jun 29, 16:30 ET | Gillette, Boston |
| 4 | Netherlands vs Morocco | Mon Jun 29, 19:00 CT | Estadio BBVA, Monterrey |
| 5 | Ivory Coast vs Norway | Tue Jun 30, 12:00 CT | AT&T, Dallas |
| 6 | France vs Sweden | Tue Jun 30, 17:00 ET | MetLife, NY/NJ |
| 7 | Mexico vs Ecuador | Tue Jun 30, 19:00 CT | Estadio Azteca, Mexico City |
| 8 | England vs DR Congo | Wed Jul 1, 12:00 ET | Mercedes-Benz, Atlanta |
| 9 | Belgium vs Senegal | Wed Jul 1, 13:00 PT | Lumen Field, Seattle |
| 10 | United States vs Bosnia & Herzegovina | Wed Jul 1, 17:00 PT | Levi's, SF Bay |
| 11 | Spain vs Austria | Thu Jul 2, 12:00 PT | SoFi, LA |
| 12 | Portugal vs Croatia | Thu Jul 2, 19:00 ET | BMO Field, Toronto |
| 13 | Switzerland vs Algeria | Thu Jul 2, 20:00 PT | BC Place, Vancouver |
| 14 | Australia vs Egypt | Fri Jul 3, 13:00 CT | AT&T, Dallas |
| 15 | Argentina vs Cape Verde | Fri Jul 3, 18:00 ET | Hard Rock, Miami |
| 16 | Colombia vs Ghana | Fri Jul 3, 20:30 CT | Arrowhead, Kansas City |

**R16 bracket (for later rounds):** W1×W4, W3×W6, W2×W5, W7×W8, W12×W11, W10×W9, W15×W14, W13×W16.

**Rule note:** 2026 wipes single group-stage yellows before the knockouts → **no yellow-accumulation
suspensions** in any R32 tie. Only ban: Cape Verde LB Sidny Lopes Cabral (red).

---

## 3. Team-form read (group stage) — sanity check for the model output

Market odds already encode all of this; use it to **cross-check** the engine, not override it.

**Favourites that looked SHAKY (temper confident/high scorelines):**
- **Germany** (vs Paraguay) — lost to Ecuador, conceded in all 3, **Schlotterbeck out (tournament)**, stars quiet; Paraguay parks the bus. Not a blowout.
- **Australia** (vs Egypt) — **books make EGYPT the favourite (~−150)**; treat tie as reversed (pending Salah fitness).
- **Belgium** (vs Senegal) & **Portugal** (vs Croatia) — genuine **coin-flips** between underwhelming favourites.
- **Switzerland** (vs Algeria) — won group but out-xG'd, finishing-variance driven.
- **Mexico** (vs Ecuador) — perfect record but efficient-not-dominant; Ecuador under-converted (not weak).

**Favourites that looked DOMINANT (best for confident scorelines + topscorers):**
- **France** (vs Sweden) — perfect 9 pts, 10 GF; Mbappé 4 & Dembélé 4. Sweden shipped 7.
- **Argentina** (vs Cape Verde) — perfect, best defence; Messi 6. (Scoring Messi-concentrated.)
- **Brazil** (vs Japan) — Vinícius hot (4); but Japan disciplined; **Raphinha OUT injured**.
- **Colombia** (vs Ghana) — under-radar dominant, out-played Portugal; under-converts (low GF); Ghana low-event.
- **Spain** (vs Austria) — 0 conceded all group; but wasteful attack, no #9 → win/clean-sheet yes, blowout no.
- **England** (vs DR Congo) — Kane 3; attack stalls vs deep blocks → low-scoring win.

**Upset risks / opponents stronger than seeded:** Egypt (fav over Australia), Norway (Haaland 4, fresh, but leaky), Croatia (Modrić, grinder), Morocco (out-played Brazil 30 min; tough for NED), Ecuador (xG under-converter), DR Congo (organised, Wissa 3).

**xG signal:** over-converters likely to regress DOWN = Mexico, Switzerland, Algeria. Under-converters likely UP = Ecuador, Colombia. Low-event attacks = Bosnia, Ghana, Paraguay.

**GK situations:** Senegal **Mendy OUT (tournament)** → backup untested (helps Belgium); Ghana Ati-Zigi groin doubt; Canada Crépeau/St. Clair unresolved.

**Low-scoring R32 profiles (cap correct-score/over confidence):** SA–Canada, Australia–Egypt, England–DRC, Spain–Austria, Colombia–Ghana.

---

## 4. Topscorer data (the 4-pick decision)

**Standout single-game value — leading shortlist (engine picks final 4 by EV under `max_ev`):**

| Rank | Player | Pos | Tie | Grp goals | Why |
|---|---|---|---|---|---|
| 1 | **Messi** | ATT | Argentina–Cape Verde | **6** (Golden Boot) | Biggest mismatch. ⚠️ CV 2 clean sheets (incl. vs Spain), Messi minutes-managed (39), missed a pen vs Austria. |
| 2 | **Kane** | ATT | England–DR Congo | 3 | Confirmed 1st PK, nailed-on, heavy fav. Cleanest "fav + pen-taker vs weak side." |
| 3 | **Oyarzabal** | ATT | Spain–Austria | 2 | Spain's #9 **and** PK; Austria leaked 6. |
| 4 | **Mbappé** | ATT | France–Sweden | 4 | PK, fully fit, Sweden shipped 7. Highest floor+ceiling. |
| 5 | **Dembélé** | ATT | France–Sweden | 4 | Hat-trick vs Norway, nailed-on, same leaky-Sweden matchup. |
| 6 | **Havertz** | ATT | Germany–Paraguay | 2 | Lone striker + de-facto PK vs weak side; Germany shaky / Paraguay low block discount. |
| DH | **Bellingham** | MID(32×) | England–DR Congo | 2 | Arrives in box; 2× mult. But minutes-managed (subbed ~60-70'). |
| DH | **De Bruyne** | MID(32×) | Belgium–Senegal | 1 | PK + FK + corners, 90 min, vs Senegal missing keeper Mendy; 2× mult. (coin-flip tie discounts team goals) |

**Discounted by tough opponents:** Haaland (Ivory Coast organised), Vinícius (Japan disciplined), Gakpo (Morocco tough).

**MUST-DROP — NOT at the tournament (hard-filter):** Foden, Palmer (Eng), Morata (Spa), Openda (Bel), Xavi Simons (Ned), Füllkrug (Ger), Rodrygo (Bra, ACL). **Raphinha OUT injured for R32** (poss. R16 return).

**Start/rotation doubts (irreducible until team-sheets, AFTER lock — bake into start-prob):** Messi (managed), Lukaku (minute-capped, likely sub), Depay (likely benched), Barcola/Thuram (bench), Leão/Endrick (super-subs), Saka (Achilles return), Yamal (managed), Gakpo (family tragedy Jun-27, staying with squad). Havertz Sofascore "injured" tag is STALE/false — treat fit, recheck at KO.

**Golden Boot race (Sofascore/Fox/ESPN, post-group):** Messi 6; then Mbappé/Dembélé/Vinícius/Haaland 4; then 3-tier: Kane, **Jonathan David (Canada — weak opp!)**, Undav (Ger super-sub), Matheus Cunha (Bra), Wissa (DRC), Sarr (Sen), Brobbey (Ned), Saibari (Mor), Manzambi (Sui).

**Uncovered high-value names worth considering (not in original candidate list):**
- **Jonathan David** (Canada, 3, nailed-on starter) vs South Africa — *tonight's match* — strong differential.
- **Matheus Cunha** (Brazil, 3, first-choice #9 with Raphinha out) vs Japan — rivals Vinícius.
- **Brobbey** (Netherlands, 3, starting #9 ahead of Depay) — outscored all listed Dutch.
- **Nuno Mendes** (Portugal, 1, **DEF 64× + free-kick taker**, nailed-on) — DEF multiplier sleeper.

**Penalty-takers (RotoWire, updated Jun-27):** confirmed 1st PK = Kane, Mbappé, Oyarzabal, Havertz (de-facto), De Bruyne, Haaland, Messi (but unreliable — missed one). Bruno Fernandes shares Portugal pens w/ Ronaldo.

---

## 5. Data sources / API plan

**The Odds API** (key in env as `$ODDS_API_KEY`; ~443/500 credits as of Jun-11):
- Competition keys (already in code): `soccer_fifa_world_cup` (h2h/spreads/totals), `soccer_fifa_world_cup_winner` (outrights).
- **Pull for the 16 R32 ties:** `markets=h2h,totals,spreads` in one featured-markets call (cheap). **`spreads` is available and currently UNUSED** — a clean margin prior worth adding.
- **ATGS:** `player_goal_scorer_anytime` via per-event endpoint (1 credit/region) — **patchy** (only some books price WC props); pull and use where posted, fall back to model g90 elsewhere.
- **NO `correct_score`, NO `to_advance` market for soccer** — confirmed twice. Keep deriving scorelines in-model (see §6).

**Sofascore (unofficial, free, no auth) — NEW high-value feed:** realized group-stage goals.
`https://www.sofascore.com/api/v1/unique-tournament/16/season/58210/top-players/overall`
(use `www.` host; `api.` host Cloudflare-403s). Fold realized goals into topscorer goal rates.

**RotoWire penalty/set-piece takers (scrape-only, all 48 teams, updated Jun-27):**
`https://www.rotowire.com/soccer/article/2026-world-cup-penalty-corner-and-free-kick-takers-by-team-114076`

**Skip standalone xG (FBref/Opta):** redundant with market odds (which embed xG), scrape-only/bot-blocked, deadline risk. The `totals`+`spreads` markets give market-implied expected goals per team for free — that's our xG-equivalent.

---

## 6. How the scoreline pick works (no guessing, no correct-score API)

`goals.py:16 goals_from_odds`: Shin de-vig the h2h 1X2 → Dixon-Coles `goal_expectancy` → (λ_home, λ_away);
rescale to the `totals` line if present. Elo fallback (`goals_from_elo`). → DC/Poisson grid → P(exact i-j)
for every cell + P(home/draw/away). `match_ev.py:20`: pick the scoreline maximising EV.

**Knockout EV (swap group 45/30 → 90/60):**
```
EV(i,j) = 60 · P(correct toto)  +  30 · P(exact i-j)
```
~90% of EV is the `60·P(toto)` term (back the right team); the exact term is a small tiebreaker that
selects the **modal low score of the most likely outcome** (typically 1-0 / 2-0 / 2-1). So draws are
~never `max_ev`-optimal, and the **advancer = the toto winner** for free.

**Knockout tweak:** result is "stand na 120 min" → for the ~20-25% of ties reaching ET, nudge expected
goals up modestly (more minutes → slightly more goals, slightly fewer draws). Negligible for heavy
favourites; matters for coin-flips. Model is backtested via LOTO CV on WC2018/22 + Euro2024 (`eval/calibrate.py`).

---

## 7. DECISIONS LOCKED

1. **Approach A** — build a knockout mode INTO the tool (reuse the goal engine), parameterised by round so R16→final are one-line re-runs. (Not a throwaway script, not manual.)
2. **`max_ev`** posture (protect the lead).
3. **Data:** pull `h2h,totals,spreads` + ATGS-where-posted for the 16 ties; pull Sofascore realized goals; transcribe key RotoWire penalty-takers. Skip standalone xG.
4. **No champion work** (Spain locked + alive).
5. Brainstorming HARD GATE: user had not yet given final "build" green light when the session paused — **confirm before implementing** (but the design above is agreed in substance).

---

## 8. BUILD PLAN (turnkey for next session)

1. **`scorito/config.py`** — add knockout constants:
   - `PTS_KO_EXACT = 90`, `PTS_KO_TOTO = 60`
   - `KO_TOPSCORER_MULT = {"GK": 64, "DEF": 64, "MID": 32, "ATT": 16}`, `KO_TOPSCORER_SLOTS = 4`
   - ET expected-goals uplift factor (e.g. effective-minutes ~1.08–1.11 on tied-at-90 mass; pick a documented default).
2. **Knockout path** (`scorito/knockout.py` + a `--phase ko_r32` flag, or extend `main.py`):
   - Load the 16 R32 ties (data file from §2).
   - Pull/replay odds for these 16; per tie → goal grid → EV-max scoreline (90/60 XOR) + advancer.
   - Topscorers: candidate pool filtered to **alive teams + in-squad** (drop §4 list), each re-pointed at their R32 opponent (single game); goal rate = blend(Sofascore realized g90, base g90) × opponent-strength × start-prob + penalty-EV term; × KO multiplier; **top-4 by EV** (max_ev).
   - Emit `out/ko_r32/{report.md, picks.csv}`, provenance-stamped.
3. **Tests:** KO XOR scoring (exact=90 not 150; toto=60); single-game topscorer EV with KO multipliers; squad/alive filter.
4. **Cross-check** output vs §3 form flags (esp. Egypt-over-Australia, coin-flips, Germany temper).
5. Offer user **pure-EV four** AND a **match-diversified variant** (mild variance cut for a lead-protector — e.g. avoid 2 from the same game like Mbappé+Dembélé).

---

## 9. FALLBACK SLATE (insurance ONLY — if the build can't run before 21:00; VERIFY vs live odds first)

Rough `max_ev` chalk from the form read. High-confidence ties marked ✅; soft ties flagged.

**Scorelines (home-away as listed in §2) + advancer:**
1. South Africa 0-1 Canada (Canada ✅adv) — *soft; ~even, Canada slight fav (David)*
2. Brazil 2-0 Japan (Brazil) — *cap it, Japan tough; 2-1 alt*
3. Germany 1-0 Paraguay (Germany) — *shaky Germany / low block; not a blowout*
4. Netherlands 2-1 Morocco (Netherlands) — *soft, Morocco strong*
5. Ivory Coast 1-1 Norway → **Norway adv** *(coin-flippy, high-event; or 1-2 Norway)*
6. France 2-0 Sweden (France) ✅
7. Mexico 1-0 Ecuador (Mexico) — *Ecuador underrated; low score*
8. England 1-0 DR Congo (England) ✅ *low-scoring*
9. Belgium 1-1 Senegal → **Belgium adv** *(coin-flip)*
10. United States 1-0 Bosnia (USA) — *low-event*
11. Spain 1-0 Austria (Spain) ✅ *clean sheet likely*
12. Portugal 1-1 Croatia → **Portugal adv** *(coin-flip)*
13. Switzerland 1-0 Algeria (Switzerland) — *soft*
14. **Australia 0-1 Egypt → EGYPT adv** *(books favour Egypt; pending Salah)*
15. Argentina 2-0 Cape Verde (Argentina) ✅ *CV stubborn; 2-1/3-0 alt*
16. Colombia 1-0 Ghana (Colombia) ✅ *low-scoring*

**Topscorers (4):** **Kane, Mbappé, Oyarzabal, Messi** (pure chalk).
- Diversified-variant swap: drop one France/ARG risk for **Dembélé** or **Havertz**; if you want the MID 2× upside, **Bellingham** for Messi.

> The fallback is hand-reasoned, NOT engine-optimised — prefer running the build. Verify scorelines against live h2h odds; the market may flip the soft ties.

---

## 9b. GROUP-STAGE RETROSPECTIVE (graded 2026-06-28 — informs R32)

Graded `out/max_ev/picks.csv` vs actual results (openfootball now has all 72 results + goalscorers;
cache refreshed; `data/wc2026_scorers.json` generated). **Grading reconciled EXACTLY to the user's
2536 pool score** (matches 1515 + standings 925 + topscorers 96 = 2536) → grader trustworthy.
Script: `scratchpad/retro.py` (in session scratch). Re-run with `.venv/bin/python -m scorito.eval
scorecard --picks out/max_ev/picks.csv` (cache + scorers file now in place).

- **Scorelines: engine WORKS — keep it.** Toto correct 46/72 (64%), 9 exact, **+420 over always-1-0
  baseline** (1515 vs 1095). Only leak: **20 actual draws, 0 predicted** (~20 of 26 misses were draws).
  Low predicted avg total (1.22 vs actual 2.99) is EXPECTED (toto term dominates → modal low score), not a bug.
- **1-0/0-1 reliance VERIFIED CORRECT (not a flaw):** we picked 1-0/0-1 on 60/72 (83%); actual was only
  10/72 (14%). But the `totals` market WAS used (797 listings) — the grid knew goals avg ~2.6-3. Under XOR,
  among same-toto scorelines 1-0 is the single most-probable cell (P(1-0)≈.13 > P(2-0)≈.11 > P(2-1)≈.09 for
  a normal favourite), so it's the EV-max exact pick. Exact-hits 9 ≈ expected (~72×0.13) → perfectly
  calibrated; exacts are just intrinsically hard. EV gap 1-0→2-1 ≈0.5pt/match (toto 30 ≫ exact upgrade 15).
  Tournament ran hot (2.99 vs ~2.6) → higher scores over-occurred (variance, not bias). R32: same 90/60 ratio
  → same low lean; ONLY the ET "120-min" uplift legitimately nudges some cells 1-0→2-1. Do NOT hard-code higher scores.
- **Scoreline R32 takeaway: KEEP 0-draw.** KO draws are rarer (~12% vs ~26%; ET breaks ties), so even with
  the doubled toto (60) backing a side stays higher-EV even in coin-flips. Have the model *report* per-tie
  draw-EV to confirm, but expect 0 draws. Pull `totals` so the grid is shaped right.
- **Topscorers: the ONE real weakness.** Ours 96 vs naive market-top-6 **168** (Mbappé/Kane/Haaland/
  **Oyarzabal/Messi**/Ronaldo). We MISSED **Messi (6 = 48 pts)** and our differentiators scored 0
  (**Wirtz MID 0**, **Raphinha 0 + injured**); Lautaro 1. Lesson: under max_ev, **do NOT pick goal-shy
  creator-mids for the multiplier — lean on penalty-takers + proven finishers.** The R32 plan's pivot to
  realized golden-boot form + single-game opponent + penalty flags is exactly the fix (would rank Messi #1,
  Wirtz nowhere). **Weight realized tournament goals heavily; exclude low-goal creators.**
- **Standings: 925/1200 (77%), 7/12 groups perfect; misses were 2nd/3rd coin-flips. No action (moot in KO).**

→ **R32 build mods:** (a) topscorer rates anchored to realized goals + penalty-taker, exclude creators;
(b) pull `totals`, report draw-EV but expect 0-draw; (c) everything else validated, keep.

## 11. FINAL R32 SLATE — BUILT & READY (generated 2026-06-28 13:19 UTC)

Knockout mode implemented (`scorito/knockout.py` + `scorito/data/knockout_fixtures.py`; KO scoring
constants in `config.py`; 9 new tests, **119 green**). Live run: `python -m scorito.knockout
--odds-key … --atgs` → 16/16 ties market-priced + full ATGS coverage (~34 credits). Output:
`out/ko_r32/{report.md,picks.csv}`. Cache split: `data/cache/worldcup2026.json` = live results;
`data/worldcup2026_fixtures.json` = committed pristine bracket for tests.

**Scorelines (advancer):** SA 0-1 Canada · Brazil 1-0 Japan · Germany 2-0 Paraguay · Netherlands 1-0
Morocco · Ivory Coast 0-1 Norway · France 2-0 Sweden · Mexico 1-0 Ecuador · England 2-0 DR Congo ·
Belgium 1-0 Senegal · USA 2-0 Bosnia · Spain 2-0 Austria · Portugal 1-0 Croatia · Switzerland 1-0
Algeria · **Australia 0-1 Egypt (Egypt advances — reversal)** · Argentina 2-0 Cape Verde · Colombia 1-0 Ghana.

**Topscorers (4, FINAL):** Messi · Mbappé · Kane · **Oyarzabal**. (Pure max-EV had Wirtz 4th at EV 12.1;
user chose Oyarzabal — higher floor / diversified / protect-the-lead. Both defensible, EV gap = noise.)

Model expected points this round ≈ 712. Remaining: user transcribes `out/ko_r32/picks.csv` into Scorito
before 21:00 CET, confirming tie orientation + late team-news in-app.

**REVIEW (2026-06-28):** dual review — independent data/math re-derivation + adversarial code review
(general-purpose agent, all 12 bug classes) — both returned **SAFE, no pick-invalidating bug**. EV math,
joins (16/16 priced), XOR scoring, multipliers, single-game goals, non-pen form blend, ET uplift, advancer
orientation all verified. Note: report "Grp goals" = NON-penalty (Kane 2 = 3 incl. a pen; Lautaro 0 = his
1 was a pen) — by design, no double-count. Added a regression guard (120 tests green).

**⚠️ R16 PREREQUISITES (fix BEFORE re-running for R16 — harmless for R32, would bite later):**
1. `knockout.py load_results_nonpen_goals` has **no round filter** — once R32+ results are appended to
   the results file, the "tournament form" blend would ingest knockout goals. Filter to completed rounds
   (or only group stage) when building R16 picks.
2. `blend_g90` hardcodes `games=3` (knockout.py) — true for all group qualifiers, but games-played
   diverges after R32. Pass actual games-played per team for R16+.
3. (Minor/optional) `run_knockout` inlines the ET-uplift instead of calling the unit-tested
   `et_adjusted_grid` (verified identical now; dedupe to avoid drift). And `INJURED_OUT` / standings /
   `R32_TIES` / `ALIVE_TEAMS` must be refreshed to the R16 bracket + latest injuries.

**For R16: re-run `python -m scorito.knockout --odds-key <key> --atgs` after the R16 bracket is set
(refresh odds + results file), having applied prereqs 1–2 above; we pick 4 fresh topscorers per round.**

## 10. RESUME CHECKLIST (next session, do in order)

1. Read this doc. Confirm time-to-lock (21:00 CET tonight) and current pool size.
2. Get user's final **green light to build** (Approach A) — design is agreed in substance.
3. Implement §8 (config constants → knockout path → tests).
4. Pull data: odds `h2h,totals,spreads` + ATGS for the 16 ties; Sofascore realized goals.
5. Generate `out/ko_r32/{report.md,picks.csv}`; cross-check vs §3.
6. Present picks (pure-EV four + diversified variant); user transcribes into Scorito before 21:00.
7. Note: per-match team-sheets drop ~1h before each game but **everything locks tonight** — can't wait for lineups; use start-probabilities.
