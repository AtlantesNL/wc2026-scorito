# Scorito WC 2026 — Topscorer research & pick recommendation

_Compiled 8 June 2026 from free/current web sources (no paid APIs). Deadline: **11 June 2026**._
_Method: a 101-agent fan-out web search (squads, odds, penalty/set-piece takers, form, xG), adversarially fact-checked (3-vote), then two per-team penalty guides fetched directly. **`g90` then re-sourced** from 2025-26 non-penalty club output (Understat npxG/90 + goals/90, FBref bot-blocked; Transfermarkt for Saudi/MLS). Findings fed the EV model in `scorito/`._

## TL;DR — recommended 6 (balanced, ~40 pool)

| # | Player | Team | Pos | Why |
|---|---|---|---|---|
| 1 | **Harry Kane** | England | ATT | elite non-pen finisher (npg/90 0.98) + #1 pen (EV 30.7) |
| 2 | **Kylian Mbappé** | France | ATT | #1 pen; lower non-pen rate than reputation (EV 24.8) |
| 3 | **Erling Haaland** | Norway | ATT | sole pen taker (EV 23.2) |
| 4 | **Lautaro Martínez** | Argentina | ATT | Serie A top scorer 25-26 (EV 22.3) |
| 5 | **Raphinha** | Brazil | ATT* | Brazil's #1 pen, factor 1.71; *MID upside (EV 21.4) |
| 6 | **Achraf Hakimi** | Morocco | **DEF** | FK/corner taker, lowest-owned, ✅ fit (played 120' CL final) — the differentiation slot (EV 17.7) |

This is five high-EV picks plus **one** low-owned differentiation defender. Alternatives for slot 6:
- **Safer defender:** Hakimi → **Van Dijk** (NED, nailed-on 38/38, aerial; EV 16.4) — higher-owned, slightly lower EV.
- **Pure EV (no differentiation):** Hakimi → **Lamine Yamal** (Spain, factor 2.00, EV 21.0). Five forwards, max raw EV (143.5), but you share it all with the field.
- **Tool `--risk balanced`** forces *both* defenders (Hakimi + Van Dijk) → 135.1 total.

_(Both open items are now resolved: positions verified — no flips — and Hakimi's hamstring is healed.)_

---

## ✅ The biggest lever — RESOLVED (positions verified in-app 8 Jun 2026)

**Checked: Raphinha, Yamal, Vinícius, Dembélé, Pulisic are all ATTACKER (no MID upside); Bellingham, Wirtz, Bruno, Valverde are MIDFIELDER — exactly as modelled. No flips, so the board below stands.** (Original analysis retained for the record:)

Points per goal are **ATT 8 / MID 16 / DEF 32 / GK 32**. MID is worth **2× ATT**. Scorito assigns each player's position, and modern wingers/10s are classified inconsistently between Aanvaller and Middenvelder. If any of these are listed **MID**, their EV roughly **doubles**:

| Player | Team | EV as ATT | EV **if MID** | Source flags him as |
|---|---|---|---|---|
| Raphinha | Brazil | 21.4 | **~42.8 (→ #1 overall)** | "Midfielder" (AllAboutFPL) |
| Lamine Yamal | Spain | 21.0 | **~42.0 (→ #1 overall)** | winger |
| Vinícius Jr | Brazil | 13.0 | **~26.1** | winger |
| Ousmane Dembélé | France | 11.8 | **~23.6** | winger/forward |

**Done (8 Jun): all checked in-app — none flipped**, so this lever is closed and the EVs above stand.

---

## What the research changed vs. the prior model

### 1. The "penalty-taking DEFENDER" edge is not supported (the prior core thesis)
Across all 48 teams, **every confirmed first-choice penalty taker is a forward or attacking-mid** — Kane (ENG), Mbappé (FRA), Ronaldo (POR), Messi (ARG), Raphinha (BRA), Oyarzabal (ESP), Haaland (NOR). The only defender data point, **Achraf Hakimi, is Morocco's #2–3 taker behind Brahim Díaz** (Soufiane Rahimi third). No full-back/wing-back/centre-back was verified as a primary taker on any side.

Quantitatively (`(g90·3·start + 0.20·pen_share)·factor·mult`), a **non-penalty** defender at g90 0.12 earns ~½ an elite striker's EV. The 32× edge only beat strikers *if* the defender took penalties — which none verifiably do. So the reserved-defender slots are a **variance / low-ownership ceiling play, not +EV**. Encoded: `pen_share` field added; Hakimi's penalty weight cut to 0.2 (kept for his real free-kick + corner duty); recommendation trimmed from 2 defenders to 1.

### 2. The 16× midfielder leverage is real but narrower than first estimated
With *estimated* g90, two midfielders cracked the top 6; with **sourced non-penalty rates**, elite strikers (Kane, Lautaro) reclaim the top and the best pure-MID picks — **Bellingham (#7)**, **Wirtz (#8)** — sit just outside the six on the 16× boost despite modest goal output. The real 16× prize is the **winger-classification lottery**: if Scorito lists **Raphinha or Yamal as MID**, they leap to ~42 EV (board-topping). Note **Bruno Fernandes fell from #4 to #13** once his actual profile (a creator: 5 non-pen goals, 21 assists, npxG/90 0.22) replaced the estimate — a caution against rating "attacking mids" on reputation. **Valverde** (URU, pens + corners) stays a useful 16× differentiator.

### 3. Penalty order corrected per team (now modelled via `pen_share`)
Portugal Ronaldo/Bruno **shared** (sources split → 0.6 / 0.5); Argentina **Messi #1** (Álvarez/Lautaro → ~0.1); Morocco **Díaz #1**, Hakimi 0.2; Germany **Havertz #1**; Belgium De Bruyne/Lukaku; Uruguay **Valverde**; Spain **Oyarzabal**; Brazil **Raphinha**; Norway **Haaland sole taker** (both per-team guides confirm — the deep-research "kill" was collateral from a bundled false conversion-% claim).

### 4. Confirmed cut/injured — excluded from the pool
**Rodrygo** (ACL), **Estêvão** (hamstring, cut), **João Pedro** (cut → Igor Thiago in), **Hugo Ekitiké** (Achilles), **Xavi Simons** (ACL), **Fermín López** (metatarsal), **Cole Palmer** (omitted), **Trent Alexander-Arnold** (omitted). None were in the pool; listed so they don't creep back in.

---

## Full ranked board (market-odds model, 8 Jun cached feed)

`fac` = team attack factor (expected group goals ÷ tournament average). `g90` = sourced 2025-26 non-penalty rate. Balanced mode reserves the 2 best DEF (Hakimi #10, Van Dijk #11).

```
 #     EV  Pos Pen   fac  Player (Team)
 1  30.71  ATT  Y   1.46  Harry Kane (England)
 2  24.84  ATT  Y   1.58  Kylian Mbappe (France)
 3  23.22  ATT  Y   1.24  Erling Haaland (Norway)
 4  22.27  ATT      1.58  Lautaro Martinez (Argentina)
 5  21.42  ATT  Y   1.71  Raphinha (Brazil)        [MID? -> ~42.8]
 6  21.02  ATT      2.00  Lamine Yamal (Spain)     [MID? -> ~42.0]
 7  20.69  MID      1.46  Jude Bellingham (England)
 8  18.21  MID      1.94  Florian Wirtz (Germany)
 9  17.90  ATT  Y   1.58  Lionel Messi (Argentina)
10  17.67  DEF      1.11  Achraf Hakimi (Morocco)       <- balanced DEF slot 1 (fit: 120' CL final)
11  16.42  DEF      1.29  Virgil van Dijk (Netherlands) <- balanced DEF slot 2
12  14.85  ATT  Y   1.51  Cristiano Ronaldo (Portugal)
13  14.83  MID  Y   1.51  Bruno Fernandes (Portugal)
14  14.60  ATT  Y   2.00  Mikel Oyarzabal (Spain)
15  14.55  DEF      1.58  Theo Hernandez (France)
16  13.21  ATT  Y   1.15  Christian Pulisic (USA)
17  13.03  ATT      1.71  Vinicius Junior (Brazil) [MID? -> ~26.1]
18  11.82  ATT      1.58  Ousmane Dembele (France) [MID? -> ~23.6]
19  11.56  ATT  Y   1.94  Kai Havertz (Germany)
20  11.47  DEF      1.94  Antonio Rudiger (Germany)
21  11.16  ATT  Y   1.20  Jonathan David (Canada)
22  10.21  MID  Y   1.17  Federico Valverde (Uruguay)
23   9.30  ATT  Y   1.33  Raul Jimenez (Mexico)
24   9.12  ATT      1.58  Julian Alvarez (Argentina)
25   8.47  MID  Y   1.43  Kevin De Bruyne (Belgium)
26   8.43  MID      2.00  Pedri (Spain)
27   7.35  ATT      1.29  Cody Gakpo (Netherlands)
28   5.15  DEF      1.58  William Saliba (France)
29   4.79  DEF      1.51  Joao Cancelo (Portugal)
```

EV sums: **max-EV top 6 = 143.5** · **balanced (2 DEF) top 6 = 135.1** · **recommended (1 DEF, Hakimi) = 140.1**.

---

## Pre-lock checklist (do on 10–11 June)
1. ✅ **Done (8 Jun):** Scorito positions verified (none flipped) and Hakimi's fitness confirmed (played 120' of the CL final).
2. **Re-pull odds + Golden Boot** (DraftKings/FanDuel/Oddschecker) and **injury/starter news** — squads locked 2 Jun but FIFA allows injury replacements up to 24h before kickoff; Mbappé & Yamal had scares that resolved.
3. **Re-run:** `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --pool-size 40 --risk balanced` (refresh `data/cache/odds_raw.json` first if you have a key).

---

## Sources (free)
- Draw & groups: [Wikipedia — 2026 WC draw](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_draw); FIFA.com.
- Outright & Golden Boot odds: [ESPN betting](https://www.espn.com/espn/betting/story/_/id/48386952/espn-soccer-futbol-world-cup-betting-odds-championship-groups); [RotoWire Golden Boot](https://www.rotowire.com/soccer/article/2026-world-cup-golden-boot-odds-full-player-list-mbappe-kane-haaland-108917); FanDuel/DraftKings via FOX/CBS/SI.
- Squads: [NBC Sports](https://www.nbcsports.com/soccer/news/2026-world-cup-squads-confirmed-rosters-for-all-48-teams); [Sky Sports](https://www.skysports.com/football/news/11095/13543070/world-cup-2026-squad-lists-england-scotland-brazil-usa-spain-france-germany-netherlands-argentina-portugal-and-more).
- Injuries/cuts: [ESPN injury tracker](https://www.espn.com/soccer/story/_/id/48572979/2026-fifa-world-cup-injuries-tracker-which-stars-miss-latest-info); [Goal.com stars missing](https://www.goal.com/en-us/lists/biggest-stars-miss-2026-world-cup-injury-suspension-selection/bltd6ff2d56ebf99a62).
- Penalty & set-piece takers (all 48): [AllAboutFPL](https://allaboutfpl.com/2026/06/fifa-world-cup-2026-penalty-and-set-piece-takers-of-all-48-teams/); [RotoWire by team](https://www.rotowire.com/soccer/article/2026-world-cup-penalty-corner-and-free-kick-takers-by-team-114076); [Oddspedia](https://oddspedia.com/insights/football/world-cup-2026-penalty-takers).
- Stats (g90): [Understat](https://understat.com/) per-player 2025-26 npxG/90 + non-pen goals/90 (pulled via the `penaltyblog` scraper since FBref returned HTTP 403); Saudi/MLS goals/90 from [Transfermarkt](https://www.transfermarkt.com/) / Wikipedia (no public xG there).

_Caveat: all odds are 5–8 June snapshots and move daily; penalty-share and start_prob figures are modelling estimates, not official depth charts. **g90 is now sourced** from 2025-26 non-penalty club output (Understat npxG/90 + goals/90, mean of the two; injury-shortened small samples shrunk toward role priors; Saudi/MLS discounted for league strength + age). g90 is club form — it does not fully capture a player's elevated national-team role, which the team factor + pen_share partly offset._
