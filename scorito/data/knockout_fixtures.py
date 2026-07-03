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
# Round of 16 (bracket structure fixed; participants = R32 winners). 13 winners are known; the 3
# from the Jul-3 ties are PRE-FILLED with the expected chalk winners — all three favourites, and
# every rival + our own R32 slate picked them to advance. >>> CONFIRM TONIGHT after the games and
# swap any upset before tomorrow's run. <<<
# ------------------------------------------------------------------------------------------------
R16_TIES = [
    Match("Canada", "Morocco", "R16", date="2026-07-04"),
    Match("Paraguay", "France", "R16", date="2026-07-04"),
    Match("Brazil", "Norway", "R16", date="2026-07-05"),
    Match("Mexico", "England", "R16", date="2026-07-05"),
    Match("Portugal", "Spain", "R16", date="2026-07-06"),
    Match("USA", "Belgium", "R16", date="2026-07-06"),
    Match("Colombia", "Egypt", "R16", date="2026-07-07"),      # PENDING: winner(Col-Gha) vs winner(Aus-Egy)
    Match("Switzerland", "Argentina", "R16", date="2026-07-07"),  # PENDING: Switzerland vs winner(Arg-CpV)
]

R16_ALIVE_TEAMS = frozenset(t for m in R16_TIES for t in (m.team1, m.team2))

# Injured/suspended out for R16 (team alive, player unavailable). Yellow-card suspensions carry into
# the KO rounds, so refresh from tomorrow's team news.
# Raphinha: R32 hamstring did NOT recover — ruled OUT for R16 vs Norway (confirmed 2026-07-03 research;
# backup Paquetá also injured, so Brazil's pen duty is now unsettled → Vinícius the likely stand-in).
R16_INJURED_OUT = frozenset({"Raphinha"})  # >>> UPDATE with tomorrow's suspension/injury news <<<

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
    ("USA", "Belgium"): "host USA (Seattle) vs an ageing Belgium — close",
}

# Pool standings entering R16 (points; gap = you - rival). >>> UPDATE after tonight's 3 games <<<.
# `diff_topscorer` = each rival's ONE non-shared topscorer (drives the lead-exposure readout).
STANDINGS = {
    "you": 3320,
    "as_of": "post-R32, PRE Jul-3 games — UPDATE after tonight",
    "rivals": [
        {"name": "#2", "points": 3244, "diff_topscorer": "Haaland (banked +16 in R32)"},
        {"name": "#3", "points": 3119, "diff_topscorer": "Brobbey (eliminated — dead slot)"},
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
