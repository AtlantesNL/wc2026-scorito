# Anytime-goalscorer market goal rates (③) — finding (2026-06-09)

## What
Replaced the hand-estimated `g90` topscorer input with **anytime-goalscorer (ATGS) market rates** from
The Odds API, where available, blended with hand `g90` as fallback. Per priced match:
`p = (1/price)/ATGS_MARGIN` (1.06), `λ = −ln(1−p)` (includes penalties + opponent → no `team_factor`/
`pen_share` re-applied); summed over a player's group games with hand `g90·start·tf` for unpriced ones.

## Coverage (2 days before kickoff)
- `/events` lists **72** group matches; **24** have `player_goal_scorer_anytime` priced now (essentially
  each team's **first** group match; later matchdays open closer to kickoff).
- **29/29** of our candidates matched after 3 aliases for the feed's full legal names
  (`Erling Braut Haaland`, `Raphael Dias Belloli`, `Pedro Gonzalez Lopez`). So every candidate is
  market-priced for ≥1 game; games 2-3 mostly fall back to hand `g90`.

## Sanity check (prices are real, no parsing bug)
| Player | priced game | price | p | λ | exp_goals | EV |
|---|---|---|---|---|---|---|
| Haaland (ATT) | vs Iraq | 1.42 | 0.67 | 1.10 | 2.87 | 22.9 |
| Kane (ATT) | vs Croatia | 2.15 | 0.44 | 0.58 | 2.94 | 23.5 |
| Mbappé (ATT) | vs Senegal | 2.08 | 0.45 | 0.61 | 2.47 | 19.7 |
| Yamal (ATT) | vs Cape Verde | 1.78 | 0.53 | 0.76 | 2.48 | 19.8 |
| Wirtz (MID) | vs Curaçao | 1.64 | 0.58 | 0.86 | 1.62 | **25.9** |
| Bellingham (MID) | vs Croatia | 4.40 | 0.21 | 0.24 | 1.10 | 17.7 |
| Hakimi (DEF) | vs Brazil/Mor | 10.0 | 0.09 | 0.10 | 0.44 | 14.0 |

All plausible bookmaker numbers (elite strikers vs minnows ~1.4-1.8; a defender ~10.0/9%).

## What the market changed
- **Kane ↓** (EV 30.7 hand → 23.5): the model assumed Kane's group-average; the market prices a *tough
  opener* (Croatia, 44%) lower.
- **Hakimi ↓** (17.7 → 14.0): the market confirms a defender's ~9% anytime prob, so even at ×32 he loses
  to a high-scoring midfielder at ×16.
- **Wirtz ↑ to #1** and **Yamal in**: real high prices in mismatched openers (Curaçao, Cape Verde) × the
  16×/8× multipliers.
- **Recommended 6:** hand → `Kane, Hakimi(DEF), Mbappé, Haaland, Bellingham(MID), Raphinha`;
  market → `Wirtz(MID), Haaland, Kane, Mbappé, Yamal, Bellingham(MID)`. Entry pool-win **9.0% → 9.3%**.

## Insight
The market **refines the multiplier thesis**: it's not "pick any high-multiplier defender" — it's pick
high-EV players at *real* scoring rates, and **high-scoring midfielders (16×)** like Wirtz/Bellingham are
the sweet spot, beating rarely-scoring defenders (×32) like Hakimi once you trust the market's ~9% on a
centre-back/wing-back.

## Caveat — re-pull near lock
Only **game-1** is priced now, so the blend tilts toward players with an **easy opener** (Wirtz/Yamal vs
minnows look strong on one priced game + two hand games). As matchdays 2-3 open (June 10-11), re-pull with
`--atgs` for a fuller, less game-1-weighted blend before transcribing — the candidate file already flags
this manual check.

## How to run
`python -m scorito.main --odds-file data/cache/odds_raw.json --atgs --odds-key "$ODDS_API_KEY" --risk balanced`
(caches `data/cache/atgs_raw.json`; replay with `--atgs-file data/cache/atgs_raw.json`, no key/credits).
