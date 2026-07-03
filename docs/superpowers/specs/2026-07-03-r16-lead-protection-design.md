# R16 pick engine — lead-protection port (design)

_Date: 2026-07-03 · Author: pairing session · Status: approved design, pre-implementation_

## Context

We are **1st** in the pool after R32 (you 3320, #2 3244, #3 3119 — lead **+76 / +201**).
Payout is **graded (1st > 2nd > 3rd)** and the goal is **protect the lead / win outright**.

Round-of-16 scoring differs from R32 (confirmed in-app):

| | Exact | Toto | ATT | MID | DEF | GK | slots |
|---|---|---|---|---|---|---|---|
| Group | 45 | 30 | 8 | 16 | 32 | 32 | 6 |
| R32 | 90 | 60 | 16 | 32 | 64 | 64 | 4 |
| **R16** | **135** | **90** | **24** | **48** | **96** | **96** | **4** |

R16 is exactly **3× group**. Crucially the two ratios are **unchanged** — exact:toto = 3:2, and
topscorer DEF/GK:MID:ATT = 4:2:1. Because the engine optimises off those *ratios*, the ported
picks keep the same *shape*; the new constants only make the reported EV and the dashboard correct.

### Opponent intelligence (visible R32 picks)

Both rivals play **pure chalk**: favourite to win every tie, star-attacker topscorers, **no
defenders/keepers, no draws**. #2 differs from us on only one topscorer (their Haaland vs our
Lautaro) and on exact scores. #3 is 201 back with a dead differential (Brobbey, eliminated).

**Strategic conclusion:** the classic leader's nightmare — a chaser punting a 96/goal defender — is
**not in play**. #2 mirrors us. Therefore *protect-the-lead = mirror the chalk*, which is exactly
what pure `max_ev` produces. We add **no** contrarian picks, keep `DEF_RESERVE = 0`, take no draws.
The only uncontrollable lever is exact-score luck; a 76-pt cushion absorbs it (~1.7 exact swings).

## Goal

Everything except the fresh odds is ready **today**, so tomorrow is one command:
`python -m scorito.knockout --round r16 --odds-key $KEY --atgs --out out/ko_r16`.

The only manual step **tonight** (not tomorrow) is confirming the 3 pending R16 participants once
Australia–Egypt, Argentina–Cape Verde, Colombia–Ghana finish (all expected chalk: Egypt, Argentina,
Colombia).

## R16 bracket (structure fixed; 3 participants pending tonight)

| # | Tie (team1 – team2) | Date | Note |
|---|---|---|---|
| 1 | Canada – Morocco | Jul 4 | |
| 2 | Paraguay – France | Jul 4 | Mbappé vs weak Paraguay |
| 3 | Brazil – Norway | Jul 5 | Haaland (#2's pick) vs Brazil |
| 4 | Mexico – England | Jul 5 | Kane vs host Mexico |
| 5 | Portugal – Spain | Jul 6 | heavyweight coin-flip |
| 6 | USA – Belgium | Jul 6 | |
| 7 | Colombia – Egypt | Jul 7 | **pending**: winner(Col–Gha) vs winner(Aus–Egy) |
| 8 | Switzerland – Argentina | Jul 7 | **pending**: Switzerland vs winner(Arg–CpV) |

## Design — additive, R32 stays byte-identical

### 1. Round-aware scoring (`config.py`)

Add a single source of truth:

```python
KO_ROUND_SCORING = {
    "Round of 32": dict(exact=90,  toto=60, mult={"GK":64,"DEF":64,"MID":32,"ATT":16},
                        slots=4, form_games=3, pen_bonus=0.07),
    "Round of 16": dict(exact=135, toto=90, mult={"GK":96,"DEF":96,"MID":48,"ATT":24},
                        slots=4, form_games=4, pen_bonus=0.07),
}
```

Existing `PTS_KO_EXACT/PTS_KO_TOTO/KO_TOPSCORER_MULT/KO_TOPSCORER_SLOTS` stay (= the R32 row), so
any code/test referencing them is unaffected. `form_games` = games played entering the round
(group 3 → +1 R32 = 4). Only R16 is added now (YAGNI; QF+ later).

### 2. Brace de-bias, ATT-only (`topscorers.py::score_candidate`)

New optional param `brace_credit` (a per-position weight table). For a market/priced candidate with
`exp_goals = λ`:

```
p1    = 1 - exp(-λ)          # P(scores at least once)
extra = λ - p1              # E[goals beyond the first]  (= E[goals] - P(≥1))
ev    = (p1 + brace_credit[pos] * extra) * mult[pos]
```

- Default `brace_credit = {"ATT":1, "MID":1, "DEF":1, "GK":1}` ⇒ `ev = λ*mult` = **current behaviour**
  (R32 output byte-identical).
- R16 passes `KO_BRACE_CREDIT = {"ATT":1.0, "MID":0.0, "DEF":0.0, "GK":0.0}` ⇒ non-ATTs credited on
  `P(≥1)` only, killing the Poisson brace inflation that lifts MIDs over strikers.

Same de-bias applied to the hand-fallback EV path (where `exp_goals` is absent, convert its λ the
same way). Add `KO_BRACE_CREDIT` to `config.py`.

### 3. Round-filter + games-played (`knockout.py::run_knockout`)

- `blend_g90(..., games=scoring["form_games"])` instead of hardcoded `3`.
- `results_file` for R16 should include **group + R32** non-penalty goals so the form blend reflects
  current form. Build/refresh `data/cache/worldcup2026_results.json` to include R32 (or accept
  group-only as a conservative fallback — the star ATTs are ATGS-priced, so the blend barely moves
  them; flag in the report which players fell back to hand g90).
- `pen_bonus=scoring["pen_bonus"]`, `mult=scoring["mult"]`, `slots=scoring["slots"]`,
  `best_scoreline(grid, pts_exact=scoring["exact"], pts_toto=scoring["toto"])`.

### 4. Round bundle threaded through `run_knockout`

Keep the signature backward-compatible (all defaults = R32):

```python
def run_knockout(ties=R32_TIES, *, alive_teams=ALIVE_TEAMS, injured_out=INJURED_OUT,
                 start_overrides=R32_START_OVERRIDES, tie_notes=TIE_NOTES,
                 round_name="Round of 32", brace_credit=None, ...):
    scoring = config.KO_ROUND_SCORING[round_name]
```

Add `R16_TIES`, `R16_ALIVE_TEAMS`, `R16_INJURED_OUT`, `R16_START_OVERRIDES`, `R16_TIE_NOTES` to
`knockout_fixtures.py`. Ties #7/#8 pre-filled with expected winners + a loud
`# CONFIRM TONIGHT (Jul-3)` comment. `R16_INJURED_OUT` starts from R32 minus resolved (Raphinha
expected back) — finalise with tomorrow's team news.

### 5. Lead-protection dashboard (`knockout.py::_write_ko_report`)

New report section driven by a small editable `STANDINGS` structure (you/#2/#3 totals + each
rival's differential topscorer). Reports, using R16 scoring units:

- Entering gap vs #2 / #3 (placeholder = current 76 / 201; **update tonight** post-games).
- Swing table: exact−toto = **+45**, ATT goal = **+24**, MID goal = **+48**, DEF/GK goal = **+96**.
- Cushion verdict: exact-differentials needed to erase the lead (~⌈76/45⌉ = 2), and a note that #2
  mirrors our chalk so realised variance is low.

Keep it lightweight — a readout, not a rival Monte-Carlo.

### 6. CLI + orchestration (`knockout.py::main`)

- `--round {r32,r16}` (default r32) → selects the fixtures bundle + round_name + brace_credit.
- Round-specific cache filenames: `data/cache/odds_{round}_raw.json`, `atgs_{round}_raw.json`
  (so R16 fetch doesn't clobber the R32 cache).
- `--out` defaults per round (`out/ko_r16` for r16).

### 7. Report strings made dynamic

`_write_ko_report` currently hardcodes "exact 90 / toto 60", "ATT 16 / MID 32 / DEF·GK 64",
"16 ties + 4 topscorers", and an R32-specific closing note. Derive all from `scoring`, `len(ties)`,
`slots`, and `tie_notes`.

### 8. Candidate coverage check (`topscorer_candidates.py`)

Verify `CANDIDATES` covers key attackers for all 16 R16 teams (esp. Portugal, Spain, Belgium,
Morocco, Mexico, USA, Switzerland, Colombia, Egypt). Add any missing before tomorrow. (Our four
picks — Messi, Mbappé, Kane, Lautaro — are all present and alive if Argentina win tonight.)

## Testing

- **R32 regression**: existing 120 tests stay green (defaults unchanged; brace_credit default = full).
- Round scoring: `best_scoreline` on a known grid pays 135/90 under R16; topscorer EV uses 24/48/96.
- Brace de-bias: a MID and an ATT with equal λ — the MID's R16 EV drops below `λ*mult`, the ATT's
  is unchanged; verify a high-λ MID no longer outranks a comparable ATT.
- R16 fixtures: `R16_TIES` well-formed (8 ties), `R16_ALIVE_TEAMS` = 16 teams, pending slots flagged.
- Dashboard: gap + swing math render from `STANDINGS`.
- Smoke: `run_knockout(round_name="Round of 16", ...)` end-to-end on saved/synthetic odds.

## Tonight (one manual step) & tomorrow's runbook

**Tonight** after the 3 games: confirm/patch ties #7/#8 participants (expected Egypt/Argentina/
Colombia) and update `STANDINGS` with the post-games gap.

**Tomorrow** (single command):
```
python -m scorito.knockout --round r16 --odds-key $KEY --atgs --out out/ko_r16
```
Then transcribe `out/ko_r16/{report.md,picks.csv}`. Cross-check: confirm R16 team news
(suspensions/injuries) moved nothing, and that our top-4 are all starting.

## Out of scope (YAGNI)

- QF/SF/final scoring rows (add when reached).
- Rival behaviour Monte-Carlo (their chalk is observed, not modelled).
- Any leverage/differentiation mode — wrong posture for a leader.
