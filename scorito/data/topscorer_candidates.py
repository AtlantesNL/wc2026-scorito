"""Seed topscorer candidate pool — g90 sourced from 2025-26 club data (8 June 2026).

``g90`` = NON-PENALTY goals per 90, set to mean(non-pen xG/90, non-pen goals/90) from
Understat for 2025-26 league play (penalties are added SEPARATELY via pen_share, so
g90 deliberately excludes them — this fixes a double-count). ``start_prob`` = chance
of starting; ``pen_taker`` = designated taker [display]; ``pen_share`` = fraction of
his team's penalties he takes [EV math; omit = 1.0 if pen_taker else 0.0].
Inline comments show the sourced numbers as ``# 25/26 npxg/npg X/Y`` (Understat,
league-only; FBref was bot-blocked). Saudi/MLS have no public xG → goals/90 with a
league+age discount. Position drives the per-goal multiplier (GK/DEF 32, MID 16, ATT 8).

CALIBRATION NOTES (what the sourced data changed vs prior estimates):
  • Mbappé's non-pen rate is much lower than reputation (8/25 LaLiga goals were pens);
    Kane is the elite non-pen finisher (npg/90 0.98). Lautaro & Pulisic were under-rated;
    Bruno (creator), Álvarez (poor season) & Oyarzabal (pen-reliant) over-rated.
  • Injury-shortened small samples (Havertz 582', De Bruyne 1176', Dembélé 1050',
    Raphinha 1424', Bellingham 1933', Hakimi 1382', Rüdiger 1501') are SHRUNK toward
    role priors — raw per-90s there are noisy.
  • npxG under-rates long-range scorers (Valverde) → those lean on actual goals/90.

⚠️ MANUAL CHECKS (deadline 11 June 2026):
  1. POSITION (biggest lever, MID 16 = 2× ATT 8) — ✅ VERIFIED in-app 8 Jun 2026:
     Raphinha, Yamal, Vinícius, Dembélé, Pulisic = ATTACKER (no MID upside);
     Bellingham, Wirtz, Bruno, Valverde = MIDFIELDER. Positions below are FINAL.
  2. FITNESS: Achraf Hakimi — ✅ RESOLVED (8 Jun): tore a hamstring late Apr 2026 but
     returned to play the FULL 120' of the Champions League final ~24 May; fit & nailed-on
     (start_prob restored to 0.95). Re-confirm the matchday XI as always.
  3. RE-PULL odds + injury/starter news on 10-11 June (FIFA allows injury replacements
     up to 24h before kickoff; Mbappé & Yamal had scares).
     ✅ 10 Jun web sweep (3 agents, ESPN tracker + official squads): NO candidate cut/out.
     Picks Kane/Wirtz/Mbappé/Haaland/Lautaro all FIT. Adjusted: Yamal 0.90→0.65 (opener doubt),
     Oyarzabal 0.80→0.55 (Jun-9 ankle, pending), Rüdiger 0.88→0.66 (benched vs USA). Hakimi FIT
     (played full CL final; ESPN tracker flag is stale). Non-candidate swaps (Timber→Geertruida,
     Karl, Wesley, Ekitiké) don't touch the pool.
     ✅ 11 Jun LOCK-DAY sweep (deep-research workflow + 5 targeted agents, adversarially
     verified): ALL SIX picks (Kane/Bellingham/Wirtz/Mbappé/Haaland/Lautaro) FIT and starting —
     Kane+Bellingham started Jun-11 Costa Rica friendly (planned subs), Wirtz consensus starter,
     Mbappé trained fully in Boston Jun 11 (Jun-7 exit = speculation, Jun-9 = authorized leave),
     Haaland clean bill (Jun-9), Lautaro 45' vs Iceland. Messi fit (20'+pen Jun 10). Adjusted:
     Oyarzabal 0.55→0.78 (scare resolved), Rüdiger 0.66→0.40 (fit, demoted to backup CB).
     No new candidate-relevant withdrawals (Balerdi/Karl/Neymar-opener don't touch the pool).

Auto-validated against squads_2026.json at runtime; confirmed CUT/INJURED & excluded:
Rodrygo, Estêvão, João Pedro, Hugo Ekitiké, Xavi Simons, Fermín López, Cole Palmer, TAA.
"""
CANDIDATES = [
    # --- Elite attackers (8×, high volume) — core EV ---------------------------
    dict(name="Harry Kane", team="England", position="ATT", g90=0.85, start_prob=0.95, pen_taker=True),                   # 25/26 npxg/npg .80/.98 Bayern (elite non-pen finisher)
    dict(name="Erling Haaland", team="Norway", position="ATT", g90=0.75, start_prob=0.95, pen_taker=True),                # 25/26 .78/.73 Man City; but Group I tempers team factor
    dict(name="Lautaro Martinez", team="Argentina", position="ATT", g90=0.68, start_prob=0.85, pen_taker=False, pen_share=0.15),  # 25/26 .70/.69 Inter, Serie A top scorer
    dict(name="Kylian Mbappe", team="France", position="ATT", g90=0.62, start_prob=0.95, pen_taker=True),                 # 25/26 .66/.58 Real Madrid (8/25 goals were pens)
    dict(name="Lionel Messi", team="Argentina", position="ATT", g90=0.55, start_prob=0.75, pen_taker=True, pen_share=0.9),# 2025 MLS npg/90 1.08 → MLS+age(39) discount. 11 Jun: hamstring = non-structural fatigue; 20'+pen goal vs Iceland (Jun 10), expected to START Jun 16 → 0.75 stands (load management)
    dict(name="Raphinha", team="Brazil", position="ATT", g90=0.55, start_prob=0.85, pen_taker=True, pen_share=0.8),       # 25/26 .56/.63 Barça (1424', hamstring); Scorito: ATT ✓; Brazil #1 pen
    dict(name="Mikel Oyarzabal", team="Spain", position="ATT", g90=0.31, start_prob=0.78, pen_taker=True, pen_share=0.85),# 25/26 .36/.26 Sociedad (7/15 goals pens); soft Group H + favourite. 11 Jun: ankle scare RESOLVED — scored vs Peru (Jun 9), played on after 29' knock, HT sub = routine rotation; no scan story anywhere, ESPN/Covers Jun-11 trackers omit him, "could miss WC" = one speculative site, RFEF leave-camp URLs are 2023/2024 → 0.55→0.78 (expected starter Jun 15)
    dict(name="Lamine Yamal", team="Spain", position="ATT", g90=0.48, start_prob=0.65, pen_taker=False, pen_share=0.1),   # 25/26 .46/.51 Barça; Scorito: ATT ✓. 11 Jun CONFIRMED: Apr-22 hamstring — available but managed: ~15' cameo opener (Barcelona cap), 45-60' game 2, full by game 3 (De la Fuente Jun 9, ESPN tracker Jun 11) → 0.65 stands (blended minutes)
    dict(name="Cristiano Ronaldo", team="Portugal", position="ATT", g90=0.45, start_prob=0.82, pen_taker=True, pen_share=0.6),  # Saudi npg/90 .76 → league+age(41) discount; soft Group K
    dict(name="Ousmane Dembele", team="France", position="ATT", g90=0.40, start_prob=0.78, pen_taker=False),              # 25/26 .37/.69 PSG (1050', shrunk); Scorito: ATT ✓
    dict(name="Vinicius Junior", team="Brazil", position="ATT", g90=0.36, start_prob=0.88, pen_taker=False),              # 25/26 .34/.38 Real Madrid; Scorito: ATT ✓
    dict(name="Julian Alvarez", team="Argentina", position="ATT", g90=0.30, start_prob=0.78, pen_taker=False, pen_share=0.1),   # 25/26 .31/.28 Atlético (down season); Messi takes ARG pens
    dict(name="Kai Havertz", team="Germany", position="ATT", g90=0.30, start_prob=0.65, pen_taker=True, pen_share=0.8),   # 25/26 only 582' (knee), shrunk; Germany #1 pen, soft Group E
    # --- Host-nation attackers (host advantage + 3 winnable group games) -------
    dict(name="Christian Pulisic", team="USA", position="ATT", g90=0.47, start_prob=0.92, pen_taker=True, pen_share=0.7), # 25/26 .49/.45 Milan; Scorito: ATT ✓
    dict(name="Jonathan David", team="Canada", position="ATT", g90=0.38, start_prob=0.90, pen_taker=True, pen_share=0.7), # 25/26 .54/.30 Juventus (underperformed xG)
    dict(name="Raul Jimenez", team="Mexico", position="ATT", g90=0.28, start_prob=0.85, pen_taker=True, pen_share=0.8),   # 25/26 .37/.20 Fulham (4/9 goals pens)
    dict(name="Cody Gakpo", team="Netherlands", position="ATT", g90=0.27, start_prob=0.82, pen_taker=False, pen_share=0.25),  # 25/26 .32/.23 Liverpool; Scorito pos unchecked (immaterial, EV 7.4)

    # --- Goal-scoring / set-piece / penalty MIDFIELDERS (16×) — leverage tier --
    dict(name="Jude Bellingham", team="England", position="MID", g90=0.32, start_prob=0.92, pen_taker=False),            # 25/26 .36/.28 Real Madrid (1933', post-surgery); Scorito: MID ✓. 11 Jun: started final warm-up vs Costa Rica at 10 (8/10); Tuchel "14-15 starters" rotation noise real (Rogers) but opener start near-certain → 0.92 stands
    dict(name="Florian Wirtz", team="Germany", position="MID", g90=0.23, start_prob=0.85, pen_taker=False),              # 25/26 .28/.19 Liverpool; soft Group E; Scorito: MID ✓
    dict(name="Bruno Fernandes", team="Portugal", position="MID", g90=0.18, start_prob=0.95, pen_taker=True, pen_share=0.5),  # 25/26 .22/.15 Man Utd (creator, 21 assists); Scorito: MID ✓; co-pen w/ Ronaldo
    dict(name="Federico Valverde", team="Uruguay", position="MID", g90=0.15, start_prob=0.95, pen_taker=True, pen_share=0.6),  # npg/90 .16 Real Madrid (xG .07 under-rates his screamers); Scorito: MID ✓; URU pens+corners
    dict(name="Kevin De Bruyne", team="Belgium", position="MID", g90=0.12, start_prob=0.75, pen_taker=True, pen_share=0.5),    # 25/26 .09/.15 Napoli (1176', hamstring surgery)
    dict(name="Pedri", team="Spain", position="MID", g90=0.10, start_prob=0.88, pen_taker=False),                        # 25/26 .10/.09 Barça (deep mid, not a scorer)

    # --- Set-piece / aerial DEFENDERS (32×) — high-ceiling differentiation -----
    # None is a confirmed first-choice penalty taker; value = open-play + set-piece × 32.
    dict(name="Achraf Hakimi", team="Morocco", position="DEF", g90=0.16, start_prob=0.95, pen_taker=False, pen_share=0.1),  # 25/26 .18/.13 PSG; FIT ✓; captain, FK+corner taker. Pen demoted 2026-07-08: Brahim Díaz is MAR #1 (Il Margine) and Hakimi MISSED his R32 shootout pen
    dict(name="Virgil van Dijk", team="Netherlands", position="DEF", g90=0.14, start_prob=0.95, pen_taker=False),         # 25/26 .13/.16 Liverpool (38 games, aerial corner threat)
    dict(name="Theo Hernandez", team="France", position="DEF", g90=0.12, start_prob=0.80, pen_taker=False),               # Saudi (Al-Hilal) g90 .16 → discount; LB
    dict(name="Antonio Rudiger", team="Germany", position="DEF", g90=0.07, start_prob=0.40, pen_taker=False),             # 25/26 .085 Real Madrid (1501', small sample); aerial CB, soft Group E. 11 Jun: FIT but DEMOTED — USA bench (Jun 6) was tactical; planned backup behind Tah/Schlotterbeck (Sport1 Jun 3, Bundesliga.com Jun 6 predicted XI) → 0.66→0.40
    dict(name="Joao Cancelo", team="Portugal", position="DEF", g90=0.06, start_prob=0.55, pen_taker=False),               # ~0 league goals 25/26 (Al-Hilal→Barça loan, rotational)
    dict(name="William Saliba", team="France", position="DEF", g90=0.04, start_prob=0.85, pen_taker=False),               # 25/26 .05/.03 Arsenal (barely scores)

    # --- R16-added: attackers for teams that advanced past R32 but were absent from the group pool.
    #     g90s are role-based estimates (⚠️ verify vs ATGS market tomorrow); ATGS λ supersedes them
    #     when priced. ⚠️ VERIFY POSITION in-app (multiplier lever): Salah/Luis Díaz likely ATT.
    dict(name="Mohamed Salah", team="Egypt", position="ATT", g90=0.55, start_prob=0.95, pen_taker=True, pen_share=0.8),   # Liverpool talisman + Egypt PK; elite non-pen threat vs Colombia
    dict(name="Luis Diaz", team="Colombia", position="ATT", g90=0.45, start_prob=0.92, pen_taker=False),                  # Bayern winger; Colombia's main goal threat
    dict(name="James Rodriguez", team="Colombia", position="MID", g90=0.14, start_prob=0.85, pen_taker=True, pen_share=0.6),  # Colombia set-pieces + PK; MID multiplier
    dict(name="Breel Embolo", team="Switzerland", position="ATT", g90=0.32, start_prob=0.80, pen_taker=False),            # Monaco #9, Switzerland's lead striker
    dict(name="Julio Enciso", team="Paraguay", position="ATT", g90=0.22, start_prob=0.60, pen_taker=False),               # scored vs Germany in R32; Paraguay's main attacking spark

    # --- 2026-07-03: in-form tournament scorers missing from the group pool (verified golden-boot
    #     research: 3+ goals) + confirmed penalty takers for R16 teams we lacked. g90 role-estimates
    #     (⚠️ ATGS market supersedes when priced). POSITIONS verified in research.
    dict(name="Folarin Balogun", team="USA", position="ATT", g90=0.40, start_prob=0.80, pen_taker=False),                 # 3 tourn goals (incl. R32 vs Bosnia); host, behind Pulisic on PKs
    dict(name="Matheus Cunha", team="Brazil", position="ATT", g90=0.35, start_prob=0.75, pen_taker=False),                # 3 tourn goals; in-form, extra weight now Raphinha is out
    dict(name="Julian Quinones", team="Mexico", position="ATT", g90=0.35, start_prob=0.78, pen_taker=False),              # 3 tourn goals; Mexico host
    dict(name="Bradley Barcola", team="France", position="ATT", g90=0.35, start_prob=0.55, pen_taker=False),              # 2 tourn goals (scored R32 vs Sweden); rotates w/ Dembélé, soft Paraguay tie
    dict(name="Ismael Saibari", team="Morocco", position="MID", g90=0.28, start_prob=0.80, pen_taker=False),              # 3 tourn goals; PSV attacking mid (MID 96 multiplier tier)
    dict(name="Johan Manzambi", team="Switzerland", position="MID", g90=0.24, start_prob=0.70, pen_taker=False),          # 3 tourn goals; Freiburg attacking mid
    dict(name="Granit Xhaka", team="Switzerland", position="MID", g90=0.10, start_prob=0.95, pen_taker=True, pen_share=0.9),   # Switzerland's PK taker (scored vs Bosnia); low open-play threat
    dict(name="Youri Tielemans", team="Belgium", position="MID", g90=0.14, start_prob=0.82, pen_taker=True, pen_share=0.45),   # de-facto BEL taker when KDB off (scored 125' PK winner vs Senegal)
    dict(name="Jhon Arias", team="Colombia", position="ATT", g90=0.30, start_prob=0.88, pen_taker=False),                 # scored the R32 winner vs Ghana (14'); Colombia's in-form wide threat
    # --- QF additions (2026-07-08 research sweep, two agents; all ATGS-priced under these plain
    #     names). Positions = best Scorito guess — VERIFY IN-APP before picking any of them
    #     (MID vs ATT doubles the multiplier). Club g90 is the blend prior; R16 goals flow in
    #     from the results supplement automatically.
    dict(name="Charles De Ketelaere", team="Belgium", position="ATT", g90=0.12, start_prob=0.85, pen_taker=False),        # 2 vs USA but Atalanta 25/26 only ~.12 npG/90 — tournament form >> club baseline
    dict(name="Romelu Lukaku", team="Belgium", position="ATT", g90=0.40, start_prob=0.40, pen_taker=False, pen_share=0.1),  # supersub consensus (2 sub goals); 25/26 lost season (quad surgery) -> 24/25 prior .39; BEL pen #2
    dict(name="Hans Vanaken", team="Belgium", position="MID", g90=0.16, start_prob=0.90, pen_taker=False),                # Brugge 7/39; club PK taker but 4th in BEL pen order
    dict(name="Mikel Merino", team="Spain", position="MID", g90=0.35, start_prob=0.55, pen_taker=False),                  # R16 winner as sub (90+1'); Arsenal .35 G/90; QF start CONTESTED (4-3-3 only)
    dict(name="Azzedine Ounahi", team="Morocco", position="MID", g90=0.25, start_prob=0.85, pen_taker=False),             # 2 vs Canada; Girona 5/24
    dict(name="Soufiane Rahimi", team="Morocco", position="ATT", g90=0.35, start_prob=0.75, pen_taker=False),             # starts if Saibari out (trending); Al Ain 9/16 heavily discounted (UAE league)
    dict(name="Brahim Diaz", team="Morocco", position="MID", g90=0.25, start_prob=0.85, pen_taker=True, pen_share=0.6),   # Morocco pen #1 (Il Margine; Hakimi #2 + missed in shootout); g90 rough est.
    dict(name="Alexander Sorloth", team="Norway", position="ATT", g90=0.42, start_prob=0.30, pen_taker=False),            # Atleti's LaLiga top scorer (13) but projected BENCH behind Haaland
    dict(name="Enzo Fernandez", team="Argentina", position="MID", g90=0.22, start_prob=0.90, pen_taker=False),            # R16 winner (90+2'); Chelsea ~8 npPL goals (Palmer takes pens)
    dict(name="Cristian Romero", team="Argentina", position="DEF", g90=0.10, start_prob=0.95, pen_taker=False),           # scored vs Egypt; set-piece CB (DEF 128 tier — chaser's punt, lead-shrink keeps him down)
    dict(name="Dan Ndoye", team="Switzerland", position="ATT", g90=0.10, start_prob=0.85, pen_taker=False),               # scored vs Algeria; Forest 1 PL goal — tournament-sharp only
]
