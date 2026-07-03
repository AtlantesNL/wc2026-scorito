# Round of 16 — handoff / runbook (2026-07-03)

**Status: engine ready.** The R16 port is coded, tested (130 green), and verified end-to-end. R32
output is byte-identical (the engine reproduces the shipped R32 picks; the brace de-bias even
reproduces the hand-tuned Lautaro-over-Bellingham call automatically). Design spec:
`docs/superpowers/specs/2026-07-03-r16-lead-protection-design.md`.

## Situation

- We are **1st**: you 3320, #2 3244 (**+76**), #3 3119 (**+201**). Payout **graded** (1st > 2nd > 3rd).
- **Objective: protect the lead / win.** For a leader this = **mirror the chalk**, take no contrarian
  picks. Both rivals play pure chalk (favourites + star ATTs, no defenders, no draws); #2 mirrors us
  almost exactly (one topscorer differs — their Haaland vs our Lautaro), #3 is remote with a dead
  differential (Brobbey, eliminated).
- R16 scoring: exact **135** / toto **90** (XOR, 120' result); topscorers **ATT 24 / MID 48 /
  DEF·GK 96**, goals this round only, excl. shootout. (Ratios identical to R32, so the max_ev pick
  *shape* is unchanged — this is why the engine ports cleanly.)

## R16 bracket

| # | Tie | Date |
|---|---|---|
| 1 | Canada – Morocco | Jul 4 |
| 2 | Paraguay – France | Jul 4 |
| 3 | Brazil – Norway | Jul 5 |
| 4 | Mexico – England | Jul 5 |
| 5 | Portugal – Spain | Jul 6 |
| 6 | USA – Belgium | Jul 6 |
| 7 | Colombia – Egypt *(pending tonight)* | Jul 7 |
| 8 | Switzerland – Argentina *(pending tonight)* | Jul 7 |

## TONIGHT — one manual step (after the Jul-3 games)

Only if an **upset** changes a pending participant, edit `scorito/data/knockout_fixtures.py`:
- Ties #7/#8 are pre-filled with the expected chalk winners **Colombia, Egypt, Argentina**. If
  Ghana / Australia / Cape Verde win instead, swap the team name (and add a topscorer candidate for
  the new team — see `topscorer_candidates.py` "R16-added" section).
- Update `STANDINGS` (you/#2/#3 points) with the post-games totals so the lead dashboard is current.
  (Everyone shares tonight's 3 winners + Messi, so the gap should hold ~+76; it ticks up if Lautaro
  scores. `R16_INJURED_OUT` — add any R16 suspensions once known.)

## TOMORROW — one command

```
python -m scorito.knockout --round r16 --odds-key $KEY --atgs --out out/ko_r16
```

Then transcribe `out/ko_r16/{report.md,picks.csv}` into Scorito. The report's **lead-protection
dashboard** shows the gap and how safe it is; picks are pure max_ev = the chalk mirror.

## Decisions to eyeball tomorrow (with real odds)

1. **Haaland (Brazil opponent).** #2 owns Haaland. Since we're protecting a lead, *matching* his
   Haaland neutralises that differential — worth a small EV sacrifice vs a higher-EV alternative
   (Lautaro/Dembélé). Check whether the market's Haaland-vs-Brazil price makes the mirror cheap.
2. **Position of Salah / Luis Díaz** — verify in-app (ATT vs MID is the multiplier lever). Added as
   ATT; if Scorito lists Salah as MID his EV jumps (48/goal).
3. **Starters** — confirm the top-4 all start; refresh `R16_INJURED_OUT` / start overrides.

## Known, deliberate limitations

- **Form-blend results file is group-only** (`worldcup2026_results.json` has no R32 goals), while
  `form_games=4`. This mildly under-credits R32 scorers *only on the hand-g90 fallback path* — the
  actual picks are ATGS-market-priced (📈), which ignores g90, so picks are unaffected. Players using
  the fallback show ✍️ in the report. (Refresh the results file with R32 goals if you want the ✍️
  fallback exact — not needed for the chalk picks.)
- No leverage/differentiation mode: intentional. A leader mirrors; only a chaser differentiates.
