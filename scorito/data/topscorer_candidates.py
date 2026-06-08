"""Seed topscorer candidate pool.

``g90`` = goals per 90 (recent-form estimate), ``start_prob`` = chance of starting,
``pen_taker`` = takes his nation's penalties. Position drives the per-goal
multiplier (GK/DEF = 32, MID = 16, ATT = 8; ratio 4:2:1), which is the whole edge:
a penalty-taking defender or wing-back on a deep-running side can out-score an
elite striker.

EDIT THIS before locking picks — late squad/injury news beats any static snapshot.
Players are auto-validated against the confirmed 2026 rosters in squads_2026.json
at runtime (see scorito/data/squads.py); anyone not in their team's squad is
dropped with a warning. Cole Palmer and Trent Alexander-Arnold were removed here
after that check showed they did not make England's final 26.
"""
CANDIDATES = [
    # --- Penalty / set-piece defenders & wing-backs (4x) ---
    dict(name="Achraf Hakimi", team="Morocco", position="DEF", g90=0.15, start_prob=0.95, pen_taker=True),
    dict(name="Virgil van Dijk", team="Netherlands", position="DEF", g90=0.12, start_prob=0.95, pen_taker=False),
    dict(name="Theo Hernandez", team="France", position="DEF", g90=0.12, start_prob=0.80, pen_taker=False),
    dict(name="William Saliba", team="France", position="DEF", g90=0.06, start_prob=0.85, pen_taker=False),
    dict(name="Joao Cancelo", team="Portugal", position="DEF", g90=0.10, start_prob=0.80, pen_taker=False),
    # --- Goal-scoring midfielders (2x) ---
    dict(name="Bruno Fernandes", team="Portugal", position="MID", g90=0.35, start_prob=0.95, pen_taker=True),
    dict(name="Jude Bellingham", team="England", position="MID", g90=0.40, start_prob=0.95, pen_taker=False),
    dict(name="Federico Valverde", team="Uruguay", position="MID", g90=0.20, start_prob=0.95, pen_taker=False),
    dict(name="Pedri", team="Spain", position="MID", g90=0.15, start_prob=0.90, pen_taker=False),
    # --- Elite attackers (1x, high volume) ---
    dict(name="Kylian Mbappe", team="France", position="ATT", g90=0.85, start_prob=0.95, pen_taker=True),
    dict(name="Harry Kane", team="England", position="ATT", g90=0.80, start_prob=0.95, pen_taker=True),
    dict(name="Erling Haaland", team="Norway", position="ATT", g90=0.90, start_prob=0.95, pen_taker=True),
    dict(name="Lamine Yamal", team="Spain", position="ATT", g90=0.45, start_prob=0.90, pen_taker=False),
    dict(name="Vinicius Junior", team="Brazil", position="ATT", g90=0.55, start_prob=0.90, pen_taker=False),
    dict(name="Lautaro Martinez", team="Argentina", position="ATT", g90=0.55, start_prob=0.85, pen_taker=False),
    dict(name="Julian Alvarez", team="Argentina", position="ATT", g90=0.50, start_prob=0.85, pen_taker=True),
    dict(name="Cristiano Ronaldo", team="Portugal", position="ATT", g90=0.55, start_prob=0.85, pen_taker=True),
]
