# Scorito World Cup 2026 — Pick Optimizer (Design Spec)

**Date:** 2026-06-08
**Goal:** Produce recommended **group-phase** Scorito entries — 72 group-match
scorelines (jointly optimized with the auto-derived group standings), **6
topscorers** (exploiting the defender position multiplier), and a **champion**
pick — tuned for a **~30–50 person pool**, **"balanced"** risk posture.

Deadline: **11 June 2026** (confirm exact lock time in-app). v1 covers the group
phase only; the tool is re-run per phase as the knockout bracket is revealed.

---

## 1. Scoring model (Scorito WK 2026, group phase)

Verified against blog.scorito.com and third-party guides. Constants centralized
in `config.py` because two are contested (flagged below).

| Component | Points | Notes |
|---|---|---|
| Exact score | **45** | per match |
| Correct toto (1/X/2) | **30** | per match |
| Group standing | **25 / correct position** | **auto-derived from your scorelines**, max **100 / group** |
| Champion bonus | **250** | only if your pick wins the tournament |
| Topscorer per goal | **DEF/GK : MID : ATT = 4 : 2 : 1** | absolute = 32/16/8 **or** 64/32/16 — **CONFIRM IN-APP** |
| Topscorer slots (group phase) | **6** (contested: blog says 4) | **CONFIRM IN-APP** |

Knockout match values (R32→Final, escalating to ~270 exact) are out of scope for
v1 but recorded in config for later phases.

## 2. Data sources

| Purpose | Source | Auth |
|---|---|---|
| Fixtures + 12 groups | `openfootball/worldcup.json` (2026, raw GitHub) | none |
| Team strength (backbone) | `eloratings.net` current ratings, all 48 teams | none (scrape) |
| Market odds | The Odds API `soccer_fifa_world_cup`, `markets=h2h,totals`, `regions=eu` | API key at runtime |
| Champion / advancement priors | Opta supercomputer (seeded dict, theanalyst.com, June 2026) + optional market blend | none |

## 3. Goal-expectancy model (verified penaltyblog 1.11.0 API)

Per match, produce `(λ_home, λ_away)` by the first available path:

1. **Odds + totals** (best): Shin de-vig the 1X2, infer supremacy; pin total
   goals from the over/under line; combine.
2. **Odds (1X2 only):** `calculate_implied(odds, method=ImpliedMethod.SHIN).probabilities`
   → `goal_expectancy(h, d, a, dc_adj=True, rho=0.001)["home_exp"/"away_exp"]`.
3. **Elo fallback** (no odds): Elo diff → expected supremacy + tournament-average
   total → `(λ_home, λ_away)`.

Score grid: `create_dixon_coles_grid(λ_home, λ_away, rho=0.001, max_goals=10)`
→ `FootballProbabilityGrid` exposing `.exact_score(i,j)`, `.home_win`, `.draw`,
`.away_win`. A pure-NumPy Poisson/DC grid implements the same interface as a
fallback (penaltyblog confirmed working, so fallback is insurance only).

*(Smoke-tested 2026-06-08: big fav→2-0, mod fav→1-0, even→1-0 — sane, and
confirms per-match EV collapses to 1-0/2-0, motivating §5.)*

## 4. Per-match EV

For grid `g`, score `(i,j)`: `EV = 45·g.exact_score(i,j) + 30·P(toto(i,j))`
where `P(toto)` is `home_win/draw/away_win`. Return **top-K** (K≈6) candidate
scorelines per match by EV.

## 5. Group optimizer (the crux — scoreline ↔ standings coupling)

Per group (4 teams, 6 matches):

1. Build the 6 score grids.
2. **Monte-Carlo** N≈20,000 sims: sample each match score from its grid; compute
   pts / goal-diff / goals-for; apply FIFA 2026 tiebreakers; record each team's
   final position → matrix `M[team, pos] = P(team finishes at pos)`.
3. Take **top-K scorelines per match** (from §4).
4. **Enumerate** the K⁶ combos (K=6 → ~46k, trivial). For each combo:
   - derive the predicted standing **deterministically** (Scorito builds the
     table from *your* predicted scores);
   - `total = Σ_matches matchEV(chosen) + Σ_pos 25·M[predicted_team_at_pos, pos]`.
   - keep the argmax.
5. Output: 6 scorelines + predicted standing + expected-points breakdown
   (match component vs standings component).

**Balanced differentiation:** among combos within ε of the best total, prefer the
one whose scorelines deviate most from the global consensus (1-0/1-1). Light,
parameterized by risk level.

**Cross-check:** a Hungarian-assignment on `M` gives the standings-only optimal
ordering; used in tests to verify the enumerator never underperforms it on the
standings component.

## 6. Champion (pool leverage)

- `P(win_t)` = blend(Opta, market) with a **double-count discount** (Opta is
  partly odds-derived; genuine independent signal is Opta Power Rankings).
- Estimate pick-share `s_t` (heuristic: inflated for the headline favourite).
- Balanced score: `P(win_t) · f(s_t)`. Recommend argmax; show **top 4** with
  `EV = P·250` and estimated share. For ~30–50 balanced the likely region is
  Spain/France — surface the trade-off (Spain over-picked → France leverage),
  user decides.

## 7. Topscorers

Editable **candidate table** (seed: Van Dijk, Saliba + other penalty/set-piece
defenders & wing-backs on deep-running teams; Mbappé, Kane, Yamal, Vinícius,
Haaland, Cunha as the attacker floor). Fields: `name, team, position, pen_taker,
g90, start_prob`.

`EV_t = (g90·3·start_prob + pen_bonus) · team_attack_factor · multiplier(position)`

where `team_attack_factor` comes from the team's expected goals across its 3
group games. Pick top 6 by EV (expected to skew toward defenders given the 4×
multiplier); show EV + rationale; user can edit before submitting.

## 8. Outputs

- `report.md` — per group: 6 scores, predicted standing, expected-points
  breakdown; champion recommendation + alternatives; 6 topscorers + EV.
- `picks.csv` — machine-readable, for fast transcription into Scorito.

## 9. Architecture (modules)

```
config.py / config.yaml   scoring constants, risk level, pool size, topscorer table
data/fixtures.py          openfootball → Group/Match objects
data/elo.py               fetch+cache Elo; normalize names to fixture teams
data/odds.py              Odds API client; map bookmaker names → team keys
data/priors.py            Opta dict + market blend
model/goals.py            (odds|elo) → (λ_home, λ_away)   [§3]
model/grid.py             create_dixon_coles_grid wrapper (+ numpy fallback) [§3]
model/match_ev.py         top-K scorelines per match    [§4]
model/group_opt.py        MC sim + K⁶ enumeration         [§5]
model/champion.py         pool-leverage champion          [§6]
model/topscorers.py       EV over candidate table         [§7]
report.py                 report.md + picks.csv           [§8]
main.py                   CLI: --risk --pool-size --odds-key/--no-odds --out
```

## 10. Testing (TDD-first on the math)

Network-free unit tests written **before** implementation for:
- `match_ev`: hand-computed small grid → known EV-optimal score.
- `grid`: λ→grid sums to 1; 1X2 internally consistent.
- `group_opt` sim: deterministic tiebreaker cases; per-position probs sum to 1;
  3-strong/1-weak group yields expected ordering.
- `group_opt` enumerator: a **constructed** group where the joint optimum differs
  from per-match argmax → optimizer must find the higher-total combo (proves the
  coupling is handled, not just asserted).
- `champion`: leverage monotonicity.
Data fetchers tested against small **recorded** fixtures (no live network in CI).

## 11. Validation / benchmarks (non-blocking)

Cross-check group sim vs `Hicruben/world-cup-2026-prediction-model` and
pouletips published fills; sanity-check score modes (1-0≈20%, 1-1≈14%; 3-1
over-picked). Large divergence = bug signal.

## 12. Risks / caveats

- **Topscorer multiplier & slot count (4 vs 6)** — confirm in-app; constants centralized.
- **Totals odds may be thin** this far out → Elo carries total-goals signal.
- **Opta/odds common source** → discounted in champion blend.
- penaltyblog 1.11.0 API verified; numpy fallback interface retained as insurance.
