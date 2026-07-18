"""Round-of-32 bracket + knockout-phase candidate adjustments (verified 2026-06-28).

Team names use the openfootball spelling used everywhere else (USA, Bosnia & Herzegovina, DR Congo,
Ivory Coast, Cape Verde) so they join cleanly with the odds feed and topscorer candidates.
"""
from scorito.types import Match

# The 16 R32 ties, in the bracket's listed order (team1 = listed-home). Neutral venues; orientation
# is nominal — picks are reported with explicit team names so transcription is unambiguous.
R32_TIES = [
    Match("South Africa", "Canada", "R32", date="2026-06-28"),
    Match("Brazil", "Japan", "R32", date="2026-06-29"),
    Match("Germany", "Paraguay", "R32", date="2026-06-29"),
    Match("Netherlands", "Morocco", "R32", date="2026-06-29"),
    Match("Ivory Coast", "Norway", "R32", date="2026-06-30"),
    Match("France", "Sweden", "R32", date="2026-06-30"),
    Match("Mexico", "Ecuador", "R32", date="2026-06-30"),
    Match("England", "DR Congo", "R32", date="2026-07-01"),
    Match("Belgium", "Senegal", "R32", date="2026-07-01"),
    Match("USA", "Bosnia & Herzegovina", "R32", date="2026-07-01"),
    Match("Spain", "Austria", "R32", date="2026-07-02"),
    Match("Portugal", "Croatia", "R32", date="2026-07-02"),
    Match("Switzerland", "Algeria", "R32", date="2026-07-02"),
    Match("Australia", "Egypt", "R32", date="2026-07-03"),
    Match("Argentina", "Cape Verde", "R32", date="2026-07-03"),
    Match("Colombia", "Ghana", "R32", date="2026-07-03"),
]

ALIVE_TEAMS = frozenset(t for m in R32_TIES for t in (m.team1, m.team2))

# ------------------------------------------------------------------------------------------------
# Round of 16 — CONFIRMED 2026-07-04 after all R32 results (verified vs FIFA/Al Jazeera/beIN
# schedules). NB the Jul-7 pairings are Argentina-EGYPT (Atlanta) and Switzerland-COLOMBIA
# (Vancouver) — the earlier pre-fill had these two ties cross-paired from a misread bracket.
# ------------------------------------------------------------------------------------------------
R16_TIES = [
    Match("Canada", "Morocco", "R16", date="2026-07-04"),        # FINAL 0-3 (toto)
    Match("Paraguay", "France", "R16", date="2026-07-04"),       # FINAL 0-1, Mbappé pen (toto)
    Match("Brazil", "Norway", "R16", date="2026-07-05"),         # FINAL 1-2, Haaland brace (zero)
    Match("Mexico", "England", "R16", date="2026-07-05"),        # FINAL 2-3 (toto)
    Match("Portugal", "Spain", "R16", date="2026-07-06"),        # FINAL 0-1, Merino 90+1' (EXACT +135)
    Match("USA", "Belgium", "R16", date="2026-07-06"),           # FINAL 1-4 (toto)
    Match("Argentina", "Egypt", "R16", date="2026-07-07"),       # FINAL 3-2 in 90', Messi 1g (toto)
    Match("Switzerland", "Colombia", "R16", date="2026-07-07"),  # FINAL 0-0 aet, SUI 4-3 pens (zero)
]

R16_ALIVE_TEAMS = frozenset(t for m in R16_TIES for t in (m.team1, m.team2))

# Injured/suspended out for R16 (team alive, player unavailable). Yellow-card suspensions carry into
# the KO rounds, so refresh from tomorrow's team news.
# Raphinha: R32 hamstring did NOT recover — ruled OUT for R16 vs Norway (confirmed 2026-07-03 research;
# backup Paquetá also injured, so Brazil's pen duty is now unsettled → Vinícius the likely stand-in).
# Balogun: RED CARD vs Bosnia (R32, 64') — one-match ban, no appeal (FIFA confirmed) → misses Belgium.
#   Cross-validated by the market: he is absent from the USA-Belgium anytime-scorer feed.
R16_INJURED_OUT = frozenset({"Raphinha", "Folarin Balogun"})  # >>> re-check team news before the lock <<<

# R16 start probabilities — R32 overrides for still-alive teams (Havertz/Germany, Depay/Netherlands
# dropped as eliminated). Refresh with tomorrow's team news / rotation reads.
R16_START_OVERRIDES = {
    "Mikel Oyarzabal": 0.90,    # Spain #9 + PK
    "Kevin De Bruyne": 0.88,    # Belgium, dead-ball duty
    "Ousmane Dembele": 0.90,    # France, red-hot
    "Vinicius Junior": 0.90,    # Brazil
    "Lautaro Martinez": 0.90,   # Argentina starting CF
    "Lionel Messi": 0.80,       # Argentina, minutes-managed
    "Cristiano Ronaldo": 0.85,  # Portugal
    "Julian Alvarez": 0.55,     # Argentina backup CF
    "Romelu Lukaku": 0.45,      # Belgium impact sub
}

R16_TIE_NOTES = {
    ("Paraguay", "France"): "Mbappé vs a low-block Paraguay — France heavy favourite",
    ("Brazil", "Norway"): "Haaland (a rival's topscorer) vs Brazil — high-quality, tighter",
    ("Mexico", "England"): "Kane vs host Mexico (Azteca altitude) — tougher than R32",
    ("Portugal", "Spain"): "Iberian heavyweight coin-flip; the two attacks cancel",
    ("USA", "Belgium"): "host USA (Seattle) vs an ageing Belgium — close; USA missing Balogun (susp.)",
    ("Argentina", "Egypt"): "Argentina laboured vs Cape Verde (3-2 AET) but Messi red-hot; Egypt drew 120' twice",
    ("Switzerland", "Colombia"): "organised vs organised; Arias/Luis Díaz the Colombia threats",
}

# ------------------------------------------------------------------------------------------------
# Quarterfinals — CONFIRMED 2026-07-08 after all R16 results. Bracket verified against four
# independent sources (Wikipedia bracket + ESPN + FOX + Al Jazeera schedules, all agreeing);
# NB the raw Wikipedia knockout-stage fetch garbles R16 winner cells — never trust it alone.
# Semis: winner QF1 vs winner QF2 (Jul-14 Dallas), winner QF3 vs winner QF4 (Jul-15 Atlanta).
# ------------------------------------------------------------------------------------------------
QF_TIES = [
    Match("France", "Morocco", "QF", date="2026-07-09"),       # Boston, 16:00 ET (= 22:00 CEST lock)
    Match("Spain", "Belgium", "QF", date="2026-07-10"),        # LA/SoFi, 15:00 ET
    Match("Norway", "England", "QF", date="2026-07-11"),       # Miami, 17:00 ET
    Match("Argentina", "Switzerland", "QF", date="2026-07-11"),  # Kansas City, 21:00 ET
]

QF_ALIVE_TEAMS = frozenset(t for m in QF_TIES for t in (m.team1, m.team2))

# Injured/suspended out for the QF (team alive, player unavailable), per 2026-07-08 evening sweep:
# - Tchouaméni (FRA): adductor tear, "would take a miracle" (Marca) — out vs Morocco (not a candidate).
# - Amadou Onana (BEL): ACL vs USA, out for tournament.
# - Jarell Quansah (ENG): straight red vs Mexico -> banned for QF vs Norway.
# - Saibari (MAR): CONFIRMED OUT — coach Ouahbi, Jul-9 presser: "Everyone's available, except
#   Saibari, with the match coming too early for him." (ESPN/Al Jazeera Jul-9). Rahimi starts.
# - Manzambi (SUI): knee, still a game-time medical call as of Jul-9 but every quote/headline leans
#   OUT ("likely to miss", Yakin: "only if... no risks involved"). Kept out.
# Doubtful only (NOT out): Nico Williams available but bench-predicted (Baena starts), Reece James
# "almost certainly not" fit (Sky Jul-9; Spence/Konsa at RB). Norway camp flu RESOLVED Jul-9 (team
# doctor: "All the players are healthy now"; Haaland never affected, trained normally Jul-9).
# Cards were wiped at the KO start and next wipe is after the QF, so a QF booking = semi ban
# (Hakimi/Rice/Bellingham/Xhaka on 1 yellow) — but nobody is suspended FOR the QF except Quansah.
QF_INJURED_OUT = frozenset({"Ismael Saibari", "Johan Manzambi"})  # lock-day verified 2026-07-09

# QF start probabilities — lock-day refresh 2026-07-09 (four-agent sweep, one per tie; Sports
# Mole/ESPN/Rotowire/Yahoo/ESPN-Argentina previews all dated Jul-8/9). Lukaku bench-predicted
# everywhere ("impact sub, lack of match fitness") — CANDIDATES 0.40 stands, no override.
QF_START_OVERRIDES = {
    "Mikel Oyarzabal": 0.90,    # confirmed starting false-9 + pen #1, zero rotation talk (Jul-9)
    "Kevin De Bruyne": 0.85,    # every Jul-8/9 predicted XI recalls him centrally
    "Ousmane Dembele": 0.90,    # France, Ballon d'Or, starts
    "Lautaro Martinez": 0.45,   # bench again per ESPN-Arg/Cadena3 Jul-9 consensus; live alternative
    "Lionel Messi": 0.85,       # full squad fit (Edul Jul-9); no minute management, no concern
    "Julian Alvarez": 0.80,     # Argentine media converge on Álvarez retaining the start (Jul-9)
}

# Slot-4 decision, LOCKED 2026-07-09 (lock day): force Haaland into the topscorer slate.
# Everyone shares Kane/Mbappé/Messi, so the QF topscorer game is slot 4 only. #3 (+259) held
# Haaland in R16 — as Norway underdog vs Brazil (in-app verified; NB rank ≠ same person across
# rounds, so R32 slates are NOT attributed to today's rivals); #2 (+118) must repick (Vinícius
# eliminated) — plausible set {Haaland, Bellingham, Oyarzabal, Dembélé, Álvarez}, and the mirror
# only loses if #2 lands on Oyarzabal specifically with P > ~2/3 (exposure model, 2026-07-09).
# Cost vs the free ranking (Oyarzabal) was −0.5 EV on Jul-8 prices, −1.0 EV on Jul-9
# lock-day prices (drift, cents-level, no ATGS move: Haaland median 2.30→2.30). Holding him zeroes
# the likeliest rival differential — the R16 regret (didn't mirror, Haaland braced, −48 vs #2) is
# the precedent this codifies. Lock-day sweep: Norway flu resolved, Haaland trained normally Jul-9.
QF_TOPSCORER_FORCED = ("Erling Haaland",)

QF_TIE_NOTES = {
    ("France", "Morocco"): "2022 semi rematch; Tchouaméni out, Saibari doubtful — Mbappé on pens",
    ("Spain", "Belgium"): "Spain scraped past Portugal 90+1'; Belgium put 4 past USA — KDB/Lukaku in form",
    ("Norway", "England"): "Haaland (7 goals) vs a Quansah-less England; Norway camp illness watch",
    ("Argentina", "Switzerland"): "Messi (8, Boot leader) vs the shootout-survivors; SUI conceded 0 in 120'",
}

# ------------------------------------------------------------------------------------------------
# Semifinals — CONFIRMED 2026-07-13 after all QF results (each tie ≥2 independent sources:
# ESPN/FOX/Al Jazeera/AP/England FA; QF actuals Fra 2-0 Mar · Esp 2-1 Bel · Nor 1-2 Eng aet ·
# Arg 3-1 Sui aet). Scoring confirmed in-app (user screenshot 2026-07-13): exact 225 / toto 150,
# topscorer ATT 40 / MID 80 / DEF·GK 160. Lock = first SF kickoff, Tue 2026-07-14 21:00 CEST.
# Third place Sat Jul-18 Miami; Final Sun Jul-19 East Rutherford.
# ------------------------------------------------------------------------------------------------
SF_TIES = [
    Match("France", "Spain", "SF", date="2026-07-14"),     # Arlington/Dallas, 15:00 ET (= 21:00 CEST lock)
    Match("England", "Argentina", "SF", date="2026-07-15"),  # Atlanta, 15:00 ET
]

SF_ALIVE_TEAMS = frozenset(t for m in SF_TIES for t in (m.team1, m.team2))

# Unavailable for the SF (Jul-12/13 sweep, two agents, ≥2 sources per claim):
# - Jarell Quansah (ENG): serves match 2 of the 2-game red-card ban — misses the SF, back for a final.
# - Jordan Henderson (ENG): arm surgery (hoarding fall celebration), bench-in-cast at best.
# Doubtful only (NOT out): Tchouaméni 50-50 (5-day plan lands on matchday; Koné the default),
# Rice trending fit (gastro bug + neural back, HT pull vs Norway), Konsa minor cramp, Romero fit
# per TyC/Edul, Medina returning-but-bench. Yellow slates were wiped after the QF — no accumulation
# bans; next amnesty n/a (final rounds).
SF_INJURED_OUT = frozenset({"Jarell Quansah", "Jordan Henderson"})

# SF start probabilities — 2026-07-13 two-agent sweep (Sports Mole/ESPN/Rotowire/KhelNow previews,
# all Jul-12/13). Consensus XIs: FRA 4-2-3-1 Maignan; Koundé-Upamecano-Saliba-Digne (Theo OUT of
# the XI); Koné-Rabiot; Dembélé-Olise-Doué behind Mbappé. ESP 4-2-3-1 Simón; Porro-Cubarsí-Laporte-
# Cucurella; Rodri-Pedri; Yamal-Olmo-Baena; Oyarzabal. ENG 4-2-3-1 Pickford; Konsa-Stones-Guéhi-
# O'Reilly; Rice-Anderson; Saka-Bellingham-Gordon; Kane. ARG diamond unchanged: E.Martínez;
# Molina-Romero-L.Martínez-Tagliafico; Paredes; De Paul-Mac Allister; Enzo; Messi-Álvarez.
SF_START_OVERRIDES = {
    # France
    "Kylian Mbappe": 0.95,      # Grade-1 ankle sprain, "completely fine", in every XI; pen #1
    "Ousmane Dembele": 0.92,    # nailed, 5 tournament goals
    "Bradley Barcola": 0.12,    # bench — Doué preferred in every predicted XI
    "Theo Hernandez": 0.12,     # lost the LB spot to Digne (all consensus XIs)
    "William Saliba": 0.95,
    # Spain
    "Mikel Oyarzabal": 0.92,    # leads the line again (false-9) in all XIs; pen #1 (8/8 since 2025)
    "Lamine Yamal": 0.92,       # nailed
    "Pedri": 0.55,              # pivot battle with Fabián Ruiz (3 of 4 sources start Pedri)
    "Mikel Merino": 0.12,       # two KO winners off the bench but in NO source's predicted XI
    # England
    "Harry Kane": 0.95,         # captain, pen #1 (WC all-time pen leader)
    "Jude Bellingham": 0.95,    # braces vs Mexico AND Norway
    # Argentina
    "Lionel Messi": 0.92,       # eye cut = zero concern; played all 120 vs SUI; pen #1 (2 misses!)
    "Julian Alvarez": 0.88,     # kept the start everywhere since the Egypt benching; QF screamer
    "Lautaro Martinez": 0.15,   # super-sub ("understudy"), sealed the QF from the bench
    "Enzo Fernandez": 0.90,
    "Cristian Romero": 0.80,    # ET fatigue/knee = cramp, fit per Edul; minority Medina scenario
}

# Slot-4 decision, LOCKED 2026-07-13 evening: force Bellingham. Current-round rival slates are
# NOT visible before the deadline (user rule 2026-07-13 — only completed rounds show), so the QF's
# "read their slate first" play is impossible; decide on our own models. Three convergent reasons:
# (1) PURE EV already ranks him #4 (ko_ev 8.3 vs Oyarzabal 6.4, devigged) — only the lead-shrink
#     demotes him, and its position-as-ownership proxy misfires here: it guards against UNDER-owned
#     MID/DEF differentials, while Bellingham (6 goals, braced in BOTH his knockout games, biggest
#     name on the hottest form) is exactly who the fame-biased field over-owns, position-blind.
# (2) Mirror math: an unmirrored rival Bellingham goal is −80, a brace −160 (the R16 Haaland regret
#     ×2). Unmirrored Oyarzabal exposure is 40×p≈6 — an order of magnitude smaller.
# (3) If rivals hold neither, we simply hold the higher-EV pick; downside ≈ 0.
# The board shuffled (mod-4 proof) so nothing is known about the new #2/#3 — this is the play that
# is least wrong across all their plausible slates. Their QF slates (visible post-deadline) can
# still be glanced at while transcribing: only BOTH-rivals-on-Oyarzabal would argue a flip.
# 2026-07-14 lock day, user's in-app QF reads: NEITHER rival held Oyarzabal — force CONFIRMED.
# #3 plays pure fame-chalk (Haaland/Kane/Mbappé/Messi; Haaland eliminated → Bellingham is their
# natural SF slot-4); #2 takes differentials (Hakimi ×128 DEF flier) — the chaser profile (2).
SF_TOPSCORER_FORCED = ("Jude Bellingham",)

# Scoreline digit-mirror, LOCKED 2026-07-14 (lock day): Fra-Esp 1-0 → 2-1. The 07-13 digit review
# left Fra-Esp a genuine coin-toss (exact mixture: 1-0 by ~1 EV at neutral tempo; price-implied
# tempo flipped it to 2-1 by 0.3 — inside noise either way) with the codified tiebreak "rival
# digits are the only signal; free to mirror". The signal arrived with the user's in-app QF reads:
# BOTH rivals played 2-1-family digits in ALL FOUR QF ties (3-1 · 2-1 · 1-2 · 2-1 — identical
# digit slates, zero clean sheets, incl. 1-2 on the Nor-Eng coin-flip). Mirroring closes the
# likeliest exact-cell differential (rival 2-1 lands = −75/rival vs our 1-0) at sub-noise EV cost.
# Eng-Arg deliberately NOT forced: the under-leaning tempo makes 1-0 robust by ~2.2 EV (digit
# review), that insurance costs real EV, and the +156/+294 lead absorbs a single exact-cell hit.
SF_SCORELINE_FORCED = {("France", "Spain"): (2, 1)}

SF_TIE_NOTES = {
    ("France", "Spain"): "Euro-24 semi rematch; Tchouaméni 50-50 (Koné default), Mbappé ankle 'fine' — Oyarzabal false-9 + pen #1",
    ("England", "Argentina"): "Quansah suspended (Konsa RB); Rice trending fit after bug; ARG diamond unchanged, Lautaro super-sub",
}

# ------------------------------------------------------------------------------------------------
# FINAL ROUND — the Final + the third-place match. CONFIRMED 2026-07-18 after both SF results
# (Spain 2-0 France [Oyarzabal 22' pen, Pedro Porro 58'] · Argentina 2-1 England [Gordon 55';
# Enzo Fernández 85', Lautaro 90+2' — Messi assist], each ≥2 independent sources: ESPN/FIFA/
# Al Jazeera/Yahoo/NPR; both settled in 90'). Scoring confirmed in-app (user paste 2026-07-18):
# exact 270 / toto 180, ATT 48 / MID 96 / DEF·GK 192 — 6x group, ONE round entry (KO_ROUND_SCORING
# ["Final"]) covers BOTH ties, 4 topscorer slots / XOR / result after 120'. The whole round locks at
# the EARLIEST kickoff = the third-place match, Sat 2026-07-18 (Miami) — so both picks are due today.
# ------------------------------------------------------------------------------------------------
FINAL_TIES = [
    Match("Spain", "Argentina", "Final", date="2026-07-19"),      # MetLife, East Rutherford NJ — the Final
    Match("France", "England", "3rd place", date="2026-07-18"),   # Hard Rock, Miami — third-place match (locks the round)
]

FINAL_ALIVE_TEAMS = frozenset(t for m in FINAL_TIES for t in (m.team1, m.team2))

# Unavailable for the FINAL round — news sweep 2026-07-18 (≥2 sources/claim; ESPN/Yahoo/SI/Al Jazeera):
# - William Saliba (FRA): back injury, subbed ~29' in the SF "in tears" — OUT of the third-place match.
# - Jordan Henderson (ENG): arm/wrist surgery (celebration fall) — OUT (not a candidate).
# - Reece James (ENG): SF muscle injury — out/doubt, Spence to RB (not a candidate).
# - Jarell Quansah (ENG): 2-game ban SERVED — AVAILABLE, likely starts the bronze match.
# Both final XIs (Spain, Argentina) are healthy — no injury doubts (Yamal minor SF scare, starts).
FINAL_INJURED_OUT = frozenset({"Jordan Henderson", "William Saliba"})

# FINAL start probabilities — news sweep 2026-07-18. FINAL (Spain/Argentina) XIs are stable & fit.
# THIRD-PLACE (France/England) is a heavily-rotated dead rubber, BUT the Golden Boot chase (Mbappé 8,
# Messi 8; Kane 6, Bellingham 6 — bronze-match goals COUNT) pins the stars in: Mbappé "no chance of
# respite" (SI), Kane projected to start in every preview. **Bellingham is a genuine game-time call**
# (started in some projected XIs, benched in others) — the single biggest lineup toss-up; the England
# XI drops ~22:00 CEST, ~1h before the 23:00 lock, so it RESOLVES before we commit slot-4.
FINAL_START_OVERRIDES = {
    # Spain (Final) — stable XI
    "Mikel Oyarzabal": 0.92,    # false-9 + pen #1; scored the SF opener (pen)
    "Lamine Yamal": 0.92,
    "Pedri": 0.15,              # fit but BENCHED since the QF (Fabián Ruiz preferred)
    "Pedro Porro": 0.90,        # RB, scored the SF second — DEF (×192 if he scores again)
    # Argentina (Final) — healthy, two selection calls
    "Lionel Messi": 0.92,       # starts; 0/2 on WC pens = live pen-duty doubt (Álvarez alternate)
    "Lautaro Martinez": 0.45,   # scored the SF winner off the bench — start vs Álvarez an open call
    "Julian Alvarez": 0.85,
    "Enzo Fernandez": 0.90,     # MID, scored the SF equaliser (×96)
    # France (third place) — CONFIRMED XI 2026-07-18 (Deschamps 7 changes): Maignan; T.Hernández,
    # Lacroix, Konaté, Gusto; Rabiot, Zaïre-Emery, Doué; Cherki, Olise, Mbappé. Dembélé BENCHED.
    "Kylian Mbappe": 0.98,      # starts — the lone star up top; France heavy favourite vs a rotated England
    "Michael Olise": 0.92,
    "Desire Doue": 0.90,
    "Ousmane Dembele": 0.18,    # BENCHED (sub only)
    # England (third place) — CONFIRMED XI 2026-07-18 (Tuchel 7 changes): D.Henderson; Quansah, Konsa,
    # Guéhi, Spence; Rice, Eze; Saka, Rogers, Rashford; Toney. KANE + BELLINGHAM BOTH BENCHED.
    "Ivan Toney": 0.90,         # leads the line for England now
    "Bukayo Saka": 0.90,
    "Marcus Rashford": 0.88,
    "Eberechi Eze": 0.90,       # MID (×96) — England's chief playmaker in this XI
    "Harry Kane": 0.18,         # BENCHED (sub) — was our slot-2 pick; ATGS feed still shows a stale starter price
    "Jude Bellingham": 0.18,    # BENCHED (sub) — the field's likely slot-4, now dead weight
    "Anthony Gordon": 0.18,     # BENCHED (sub)
}

# Slot-4 = CHERKI, LOCKED 2026-07-18 (final lock recheck). Evolution this evening: confirmed XIs
# benched Kane (our morning slot-2) AND Bellingham (field's likely slot-4) — Tuchel/Deschamps 7 changes
# each. Oyarzabal-over-Bellingham paid off (their slot-4 benched, ours starts the final). Benched Kane
# first swapped to Yamal (fame-mirror), then to CHERKI once the pool confirmed him a MIDFIELDER (×96):
# a full Fable-model re-analysis put Cherki at EV 15.9 (starter #10 behind Mbappé in a France rout) vs
# Yamal 9.0 — a +6.9 upgrade the fame field can't punish (its likely 4th picks Kane/Bellingham are
# benched cameos). Kept the ×192 lottery defenders (Théo 14.4, Porro 9.7) OUT — chaser plays; we lead
# +151 and only need to mirror the two names that can hurt us (Mbappé, Messi) + Oyarzabal's pen floor.
# Final topscorers: Mbappé / Cherki / Messi / Oyarzabal. (Entered in-app by the user.)
FINAL_TOPSCORER_FORCED = ("Rayan Cherki",)
FINAL_SCORELINE_FORCED = {}

FINAL_TIE_NOTES = {
    ("Spain", "Argentina"): "THE FINAL — Spain (beat France 2-0) vs Argentina (beat England 2-1); Yamal/Oyarzabal/Pedri vs Messi/Álvarez/Enzo; settles after 120' then pens",
    ("France", "England"): "third-place match — France (lost 0-2 Spain) vs England (lost 1-2 Argentina); rotation + dead-rubber intensity risk; Mbappé/Dembélé vs Kane/Bellingham",
}

# Pool standings entering the FINAL round — reported by the user 2026-07-18 (SF complete; rival SF
# slates now VISIBLE, completed-round rule). You scored 0 in the SF but HELD the lead: the chalk field
# largely blanked with you. What ALL of us shared and busted: a France advancer (Fra 2-1 or 1-0, all
# wrong — Spain won) and the Kane/Mbappé/Bellingham topscorer core (all blanked). Your 4631 is
# unchanged from pre-SF, confirming the 0-point SF retro exactly.
# Rival SF slates, graded against SF scoring (exact 225 / toto 150, ATT 40 / MID 80):
#   #2 iamtope 4480 (+225): Fra 2-1 (0) · Eng-Arg 1-2 EXACT (+225) · Kane/Mbappé/Messi/Bellingham (0)
#      — the ONE differential that closed ground: they nailed the exact ARGENTINA scoreline.
#   #3 neemaar jr 4475 (+0): Fra 2-1 (0) · Eng-Arg 1-1 draw pick (0) · Doué/Kane/Mbappé/Bellingham (0).
#   #4 thomneleman 4377 (+40): Fra 1-0 (0) · Eng-Arg 2-1 (0) · Dembélé/Kane/Mbappé/Bellingham — the
#      +40 (one ATT goal) does NOT reconcile with the four names given (all blanked): minor
#      transcription slack, immaterial at −254.
# Mirror grade: Bellingham force + Fra-Esp 2-1 digit mirror both cost 0 — France lost so that tie was
# moot, and everyone held Bellingham. Insurance refunded, as at the QF.
# CORRECTED read (Fable review 2026-07-18, de-vig checked): both SF ties were near-coin-flips and we
# picked the SLIGHT FAVOURITES — de-vig 90' Eng 36.3/dr 32.1/Arg 31.6 (Eng favoured), Fra 38.5/dr 31.0/
# Esp 30.5 (Fra favoured) — and both lost (ordinary variance, not an underdog blunder). iamtope gained
# by hitting an UNDERDOG exact (+225), a low-probability hit, NOT a favoured-vs-underdog edge. So there
# is no directional "favoured advancer" lesson. For the Final, back Spain because it is a CLEAR
# favourite (120' grid Spain 54 / draw 13.5 / Arg 33; ~61% incl. pens) — not a coin-flip like the SFs.
STANDINGS = {
    "you": 4631,
    "as_of": "SF complete (user-reported 2026-07-18); rival SF slates read in-app",
    "rivals": [
        {"name": "#2 iamtope", "points": 4480, "diff_topscorer": "SF +225 (Eng-Arg 1-2 exact) — the only mover; pure fame-chalk topscorers. LIVE THREAT at −151, one exact-vs-your-miss from level."},
        {"name": "#3 neemaar jr", "points": 4475, "diff_topscorer": "SF blank; fame-chalk + Doué flier. −156."},
        {"name": "#4 thomneleman", "points": 4377, "diff_topscorer": "SF ~blank; fame-chalk (Dembélé/Kane/Mbappé/Bellingham). −254."},
    ],
}

# Injured/out for the R32 round specifically (team still alive, player unavailable this round).
INJURED_OUT = frozenset({"Raphinha"})  # hamstring vs Haiti; eyeing R16. (Brazil advances.)

# R32-specific start probabilities, overriding the group-phase values where the post-group team news
# changed (group values carried pre-tournament injury-scare discounts that have since resolved, or
# rotation reads from the knockout previews). Sourced from the 2026-06-28 research sweep.
R32_START_OVERRIDES = {
    "Mikel Oyarzabal": 0.90,    # nailed-on #9 + PK, fully fit (group 0.78 = resolved ankle scare)
    "Kai Havertz": 0.85,        # nailed-on lone striker; Sofascore "injured" tag is stale/false
    "Kevin De Bruyne": 0.88,    # nailed-on ~90' starter, dead-ball duty vs Senegal
    "Ousmane Dembele": 0.90,    # nailed-on, red-hot (hat-trick vs Norway)
    "Vinicius Junior": 0.90,    # healthy, nailed-on
    "Lautaro Martinez": 0.90,   # nailed-on starting CF
    "Lionel Messi": 0.80,       # expected start, minutes-managed (age 39)
    "Cristiano Ronaldo": 0.85,  # nailed-on
    "Julian Alvarez": 0.55,     # backup CF behind Lautaro
    "Romelu Lukaku": 0.45,      # fit but minute-capped, likely impact sub
    "Memphis Depay": 0.30,      # fitness-managed, projected to start on the bench
}

# Form cross-check notes for the report (from the group-stage form read; market odds already price these).
TIE_NOTES = {
    ("Australia", "Egypt"): "⚠️ books favour EGYPT (Salah fitness the swing); bracket order is reversed",
    ("Belgium", "Senegal"): "coin-flip; Senegal missing keeper Mendy",
    ("Portugal", "Croatia"): "coin-flip; both underwhelmed in groups",
    ("Switzerland", "Algeria"): "close; Switzerland over-converted, Algeria leaky (7 GA)",
    ("Germany", "Paraguay"): "Germany shaky (lost to Ecuador, Schlotterbeck out); Paraguay low block",
    ("Netherlands", "Morocco"): "Morocco strong (out-played Brazil); NED conceded in all 3",
    ("Mexico", "Ecuador"): "Ecuador under-converted xG — not a soft out",
    ("Ivory Coast", "Norway"): "high-event; Haaland hot but IVC organised",
}
