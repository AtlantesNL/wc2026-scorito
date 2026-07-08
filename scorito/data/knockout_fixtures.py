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

# Injured/suspended out for the QF (team alive, player unavailable), per 2026-07-08 research sweep:
# - Tchouaméni (FRA): adductor recurrence, out vs Morocco (not a candidate; listed for completeness).
# - Amadou Onana (BEL): ACL vs USA, out for tournament.
# - Jarell Quansah (ENG): straight red vs Mexico -> banned for QF vs Norway.
# Doubtful, re-check on lock day: Saibari (MAR hamstring, MRI — candidate!), Nico Williams (ESP
# adductor, bench-only), Manzambi (SUI knee — candidate!), Reece James (ENG hamstring, likely sub);
# Norway camp illness (Strand Larsen +others, improving). Cards were wiped at the KO start and next
# wipe is after the QF, so a QF booking = semi ban (Hakimi/Rice/Bellingham/Xhaka etc. on 1 yellow)
# — but nobody is suspended FOR the QF except Quansah.
QF_INJURED_OUT = frozenset({"Ismael Saibari", "Johan Manzambi"})  # doubtful-out; >>> re-check before lock <<<

# QF start probabilities — refresh with lock-day team news. Eliminated-team overrides dropped.
QF_START_OVERRIDES = {
    "Mikel Oyarzabal": 0.90,    # Spain #9 + PK (started R16, subbed 90+7')
    "Kevin De Bruyne": 0.88,    # Belgium, dead-ball duty
    "Ousmane Dembele": 0.90,    # France
    "Lautaro Martinez": 0.75,   # Argentina — BENCHED in R16 (sub 66'); re-read lock-day lineups
    "Lionel Messi": 0.85,       # started + scored R16; no fitness noise
    "Julian Alvarez": 0.60,     # started R16 ahead of Lautaro
    "Romelu Lukaku": 0.45,      # Belgium impact sub (scored 90+2' vs USA)
}

QF_TIE_NOTES = {
    ("France", "Morocco"): "2022 semi rematch; Tchouaméni out, Saibari doubtful — Mbappé on pens",
    ("Spain", "Belgium"): "Spain scraped past Portugal 90+1'; Belgium put 4 past USA — KDB/Lukaku in form",
    ("Norway", "England"): "Haaland (7 goals) vs a Quansah-less England; Norway camp illness watch",
    ("Argentina", "Switzerland"): "Messi (8, Boot leader) vs the shootout-survivors; SUI conceded 0 in 120'",
}

# Pool standings entering the QF. YOUR points = 3486 + 633 banked in R16 (exact Por 0-1 Esp = 135,
# 5 totos = 450, Mbappé+Messi = 48). Rival R16 rounds are NOT yet known — the numbers below assume
# they full-mirrored our scorelines (585) and #2 played the Kane/Haaland chalk slate (+120 ts) while
# #3 banked ~72 ts. >>> REPLACE with the in-app leaderboard before the QF lock — this is the input
# to the lead dashboard and the mirror-vs-EV topscorer call. <<<
STANDINGS = {
    "you": 4119,
    "as_of": "R16 complete (projected; VERIFY IN-APP before QF lock)",
    "rivals": [
        {"name": "#2", "points": 4085, "diff_topscorer": "Haaland (7 goals — Norway ALIVE, QF vs England)"},
        {"name": "#3", "points": 3900, "diff_topscorer": "unknown — re-read their R16 slate in-app"},
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
