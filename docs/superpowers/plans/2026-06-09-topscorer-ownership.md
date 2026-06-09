# Topscorer ownership (fame bias) — Implementation Plan (Approach B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Select the 6 topscorers that maximize P(finishing 1st) against a realistic fame-biased field (rivals over-own famous attackers, under-own high-multiplier DEF/GK), replacing the EV+reserve heuristic on the main path.

**Architecture:** A `fame_score` (EV without the position multiplier) drives the field's rival topscorer picks; a pure `greedy_topscorers` core selects our 6 by pool-win (greedy + swap, additive O(worlds) scoring); a `pool_win_topscorers` wrapper samples worlds + field and runs it; `main` wires it for balanced/aggressive.

**Tech Stack:** Python 3.12, numpy, pytest. No new deps, no new config.

---

## Task 1: `fame_score` (drop the multiplier for rival weighting)

**Files:** Modify `scorito/model/topscorers.py`, `tests/test_topscorers.py`

- [ ] **Step 1: Failing test** — append to `tests/test_topscorers.py`:
```python
def test_fame_score_drops_multiplier():
    from scorito.model.topscorers import fame_score, score_candidate
    tf = {"T": 1.0}
    att = dict(name="A", team="T", position="ATT", g90=0.5, start_prob=1.0)
    dfn = dict(name="D", team="T", position="DEF", g90=0.125, start_prob=1.0)
    # equal expected GOALS*4 vs *1 -> equal Scorito EV, but fame (goals only) is 4x for the attacker
    assert abs(score_candidate(att, tf) - score_candidate(dfn, tf)) < 1e-9
    assert abs(fame_score(att, tf) - 4 * fame_score(dfn, tf)) < 1e-9
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_topscorers.py::test_fame_score_drops_multiplier -q` → FAIL (no `fame_score`).
- [ ] **Step 3: Implement** — in `scorito/model/topscorers.py`, after `score_candidate` add:
```python
def fame_score(c, team_factors) -> float:
    """Rival-ownership weight: expected group-phase goals * team factor, WITHOUT the position
    multiplier — models amateurs chasing famous scorers and ignoring that a DEF/GK goal is worth 4x.
    So attackers get over-owned and high-multiplier defenders/keepers under-owned."""
    pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
    expected_goals = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
    return expected_goals * team_factors.get(c["team"], 1.0)
```
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add scorito/model/topscorers.py tests/test_topscorers.py && git commit -m "feat(topscorers): fame_score (EV without the position multiplier) for rival weighting"`

## Task 2: `greedy_topscorers` pure core

**Files:** Modify `scorito/model/pool.py`, `tests/test_pool.py`

- [ ] **Step 1: Failing test** — append to `tests/test_pool.py` (numpy is imported there as `np`; if not, add `import numpy as np`):
```python
def test_greedy_topscorers_picks_underowned_high_variance():
    from scorito.model.pool import greedy_topscorers
    our_fixed = np.array([8.0, 8, 8, 8])
    max_rival = np.array([10.0, 10, 10, 10])
    points = {
        "striker": np.array([1.0, 1, 1, 1]),   # always +1 -> 9 < 10, never wins (commoditized)
        "defender": np.array([0.0, 0, 0, 5]),   # spikes in world 4 -> 13 > 10 there
    }
    names, pwin = greedy_topscorers(our_fixed, max_rival, points, n_slots=1)
    assert names == ["defender"] and abs(pwin - 0.25) < 1e-9

def test_greedy_topscorers_no_field_reduces_to_ev():
    from scorito.model.pool import greedy_topscorers
    our_fixed = np.zeros(4)
    max_rival = np.full(4, -np.inf)            # no rivals -> every pick wins; tie-break by EV
    points = {"lo": np.array([1.0, 1, 1, 1]), "hi": np.array([2.0, 2, 2, 2])}
    names, pwin = greedy_topscorers(our_fixed, max_rival, points, n_slots=1)
    assert names == ["hi"] and pwin == 1.0
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_pool.py -k greedy_topscorers -q` → FAIL (no `greedy_topscorers`).
- [ ] **Step 3: Implement** — in `scorito/model/pool.py`, after `champion_win_probs` add:
```python
def greedy_topscorers(our_fixed, max_rival, points_by_name, n_slots):
    """Select n_slots names maximizing P(our_fixed + sum_picked > max_rival), tie-broken by expected
    points (so a fieldless max_rival=-inf reduces to EV-greedy). Greedy forward-select, then a
    coordinate-ascent swap pass that fires only on strict pool-win gains. our_fixed[W], max_rival[W]
    numpy; points_by_name {name: ndarray(W)} = multiplier*goals. Returns (picked_names, pool_win)."""
    names = list(points_by_name)

    def pwin(w):
        return float(np.mean(our_fixed + w > max_rival))

    chosen, ts_w = [], np.zeros_like(our_fixed, dtype=float)
    for _ in range(min(n_slots, len(names))):
        best = max((n for n in names if n not in chosen),
                   key=lambda n: (pwin(ts_w + points_by_name[n]), float(points_by_name[n].sum())))
        chosen.append(best)
        ts_w = ts_w + points_by_name[best]
    improved = True
    while improved:
        improved = False
        for i in range(len(chosen)):
            base = ts_w - points_by_name[chosen[i]]
            options = [n for n in names if n == chosen[i] or n not in chosen]
            best = max(options, key=lambda n: (pwin(base + points_by_name[n]),
                                               float(points_by_name[n].sum())))
            if best != chosen[i] and pwin(base + points_by_name[best]) > pwin(ts_w) + 1e-12:
                ts_w = base + points_by_name[best]
                chosen[i] = best
                improved = True
    return chosen, pwin(ts_w)
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_pool.py -k greedy_topscorers -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/model/pool.py tests/test_pool.py && git commit -m "feat(topscorers): greedy_topscorers pool-win selection core"`

## Task 3: `pool_win_topscorers` wrapper

**Files:** Modify `scorito/model/pool.py`

(Glue over `sample_worlds`/`generate_field`/`score_field` + `greedy_topscorers`; validated by the real run in Task 5 — a unit test would need the full 12-group bracket fixture.)

- [ ] **Step 1: Add the `score_candidate` import** — in `scorito/model/pool.py` change
`from scorito.model.topscorers import sample_player_goals` to:
```python
from scorito.model.topscorers import sample_player_goals, score_candidate
```
- [ ] **Step 2: Implement** — after `greedy_topscorers` add:
```python
def pool_win_topscorers(our_entry, our_champion, candidates, gteams, group_matches, grids, elo,
                        bracket, team_factors, champion_probs, scoreline_choices, ts_field_pool,
                        pool_size, n_slots=config.TOPSCORER_SLOTS, seed=0, sims=config.POOL_WIN_SIMS,
                        bonus=config.CHAMPION_BONUS):
    """Pick n_slots topscorers maximizing P(our entry finishes 1st), holding scorelines + champion
    fixed, against a fame-weighted field. Returns (picks: candidate dicts with 'ev', pool_win)."""
    worlds = sample_worlds(gteams, group_matches, grids, elo, bracket, candidates, team_factors,
                           sims=sims, seed=seed)
    field = generate_field(max(0, pool_size - 1), scoreline_choices, champion_probs, ts_field_pool,
                           config.FIELD_SHARPNESS, np.random.default_rng(seed + 1))
    base_excl, rival_base, rival_champ, champ_w = score_field(
        dict(our_entry, topscorers=[]), field, worlds, gteams, group_matches)
    W = len(worlds)
    if rival_base.shape[0] == 0:
        max_rival = np.full(W, -np.inf)
    else:
        rc = np.array(rival_champ, dtype=object)[:, None]
        max_rival = (rival_base + bonus * (rc == champ_w[None, :])).max(axis=0)
    our_fixed = base_excl + bonus * (champ_w == our_champion)
    pgoals_arr = {n: np.array([w["pgoals"][n] for w in worlds], dtype=float) for n in worlds[0]["pgoals"]}
    points = {c["name"]: config.TOPSCORER_MULT[c["position"]] * pgoals_arr[c["name"]] for c in candidates}
    names, pwin = greedy_topscorers(our_fixed, max_rival, points, n_slots)
    by_name = {c["name"]: c for c in candidates}
    picks = [dict(by_name[n], ev=round(score_candidate(by_name[n], team_factors), 3)) for n in names]
    return picks, pwin
```
- [ ] **Step 3: Run** `.venv/bin/python -m pytest -q` → PASS (import + new function don't break anything).
- [ ] **Step 4: Commit** `git add scorito/model/pool.py && git commit -m "feat(topscorers): pool_win_topscorers wrapper (worlds + fame field -> greedy)"`

## Task 4: wire into `main.py` + report, fame-field test

**Files:** Modify `scorito/main.py`, `scorito/report.py`, `tests/test_field.py`

- [ ] **Step 1: Failing test (fame field over-owns attackers)** — append to `tests/test_field.py`:
```python
def test_fame_weighted_field_overowns_attackers():
    from scorito.model.topscorers import fame_score
    cp = {"X": 1.0}
    sc = {("A", "B"): [((1, 0), 1.0)]}
    tf = {"T": 1.0}
    att = dict(name="Att", team="T", position="ATT", g90=0.5, start_prob=1.0)
    dfn = dict(name="Def", team="T", position="DEF", g90=0.125, start_prob=1.0)  # equal EV to Att
    fillers = [dict(name=f"F{i}", team="T", position="ATT", g90=0.1, start_prob=1.0) for i in range(8)]
    cands = [att, dfn] + fillers
    ts_pool = [(c, fame_score(c, tf)) for c in cands]
    entries = fld.generate_field(500, sc, cp, ts_pool, sharpness=2.0, rng=np.random.default_rng(0))
    own = lambda nm: sum(1 for e in entries if any(t["name"] == nm for t in e["topscorers"]))
    assert own("Att") > own("Def")     # equal Scorito EV, but fame over-owns the attacker
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_field.py::test_fame_weighted_field_overowns_attackers -q` → PASS already (it exercises existing `generate_field` with `fame_score` from Task 1; this locks the field behaviour). If `fld`/`np` not imported in the file, they are (top of `tests/test_field.py`).
- [ ] **Step 3: Init `ts_pool_win`** — in `scorito/main.py`, find `advance, pool_win, pool_win_stable = {}, {}, True` and change to:
```python
    advance, pool_win, pool_win_stable, ts_pool_win = {}, {}, True, None
```
- [ ] **Step 4: Import `fame_score`** — change `from scorito.model.topscorers import score_candidate` (inside the `len(gteams)==12` block) to:
```python
        from scorito.model.topscorers import fame_score, score_candidate
```
- [ ] **Step 5: Fame field pool + champion call** — replace
```python
        ts_pool = [(c, score_candidate(c, team_factors)) for c in kept]
        contenders = sorted({t for t, p in pwin.items() if p >= 0.02} | {champion[0].team})
        best, pool_win, pool_win_stable = pool.pool_win_champion(
            our_entry, gteams, group_match_keys, all_grids, elo_map, brk, kept,
            team_factors, pwin, scoreline_choices, ts_pool, pool_size, contenders, seed=seed)
        champion = sorted(champion, key=lambda r: (r.team != best, -pool_win.get(r.team, 0.0)))
```
with:
```python
        ts_field_pool = [(c, fame_score(c, team_factors)) for c in kept]
        contenders = sorted({t for t, p in pwin.items() if p >= 0.02} | {champion[0].team})
        best, pool_win, pool_win_stable = pool.pool_win_champion(
            our_entry, gteams, group_match_keys, all_grids, elo_map, brk, kept,
            team_factors, pwin, scoreline_choices, ts_field_pool, pool_size, contenders, seed=seed)
        champion = sorted(champion, key=lambda r: (r.team != best, -pool_win.get(r.team, 0.0)))
        if risk != "max_ev":
            topscorers, ts_pool_win = pool.pool_win_topscorers(
                dict(our_entry, champion=best), best, kept, gteams, group_match_keys, all_grids,
                elo_map, brk, team_factors, pwin, scoreline_choices, ts_field_pool, pool_size, seed=seed)
```
- [ ] **Step 6: Surface in meta** — change the `meta=` line in the `RunResult(...)` to:
```python
        meta={"pool_win_stable": pool_win_stable, "pool_win_sims": config.POOL_WIN_SIMS,
              "ts_pool_win": ts_pool_win},
```
- [ ] **Step 7: Report note** — in `scorito/report.py`, after the topscorer intro append (the block ending `"group-phase points.\n")`), add:
```python
    if result.meta.get("ts_pool_win") is not None:
        L.append(f"_Engine-selected to maximize P(finishing 1st)_ vs a fame-biased field "
                 f"(over-owns famous attackers); entry pool-win {result.meta['ts_pool_win']:.1%}.\n")
```
- [ ] **Step 8: Run** `.venv/bin/python -m pytest -q` → PASS.
- [ ] **Step 9: Commit** `git add scorito/main.py scorito/report.py tests/test_field.py && git commit -m "feat(topscorers): wire engine selection + fame field into main/report"`

## Task 5: real run, pool-win uplift evidence, README

**Files:** Create `docs/topscorer-ownership-calibration-2026-06-09.md`; Modify `README.md`; verification

- [ ] **Step 1: Real run** — `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --risk balanced`. Expected: completes; the topscorer table shows the engine leaning into ≥1 under-owned high-multiplier DEF/GK vs the old EV+reserve list; champion cluster unchanged (Argentina/Portugal); report shows the entry pool-win line.
- [ ] **Step 2: Pool-win uplift evidence** — run this diagnostic (engine-selected 6 vs the `pick_topscorers` EV+reserve baseline, SAME worlds/field/champion):
```bash
.venv/bin/python - <<'PY'
import json
from collections import defaultdict
import numpy as np
from scorito.data import elo, fixtures, squads as sq, odds as om
from scorito.data.fixtures import group_teams
from scorito.data.topscorer_candidates import CANDIDATES
from scorito import config
from scorito.model.goals import expected_goals
from scorito.model.grid import build_grid
from scorito.model.group_opt import optimize_group
from scorito.model import field as fld, pool, tournament, bracket as bk
from scorito.model.match_ev import topk_scorelines
from scorito.model.topscorers import pick_topscorers, score_candidate, fame_score
from scorito.data.priors import blended_probs, blend_champion_probs
from scorito.main import _default_fixtures
src = _default_fixtures(); matches = fixtures.load_fixtures(src); gteams = group_teams(matches)
ats = sorted({t for ts in gteams.values() for t in ts}); em = elo.get_elo(ats)
eg = dict(em)
for h in config.HOSTS:
    if h in eg: eg[h] += config.HOST_ELO_BONUS
omap = om.parse_odds(json.load(open("data/cache/odds_raw.json")))
allg = {}; tl = defaultdict(list); gr = {}
for g, ts in gteams.items():
    gm = [m for m in matches if m.group == g]; gmk = [(m.team1, m.team2) for m in gm]; grd = {}
    for m in gm:
        l1, l2 = expected_goals(m, omap, eg); allg[(m.team1, m.team2)] = build_grid(l1, l2)
        grd[(m.team1, m.team2)] = allg[(m.team1, m.team2)]; tl[m.team1].append(l1); tl[m.team2].append(l2)
    obm = {k: fld.scoreline_ownership(grd[k], config.DRAW_AVERSION, config.FIELD_SHARPNESS) for k in grd}
    gr[g] = optimize_group(ts, gmk, grd, k=config.TOPK_SCORELINES, sims=4000, seed=0, group=g,
                           own_by_match=obm, n_rivals=31, gamma=config.SCORELINE_LEVERAGE_GAMMA["balanced"])
means = {t: sum(v)/len(v) for t, v in tl.items()}; avg = sum(means.values())/len(means)
tf = {t: means[t]/avg for t in means}
gmk = [(m.team1, m.team2) for m in matches]; brk = bk.load_bracket(src)
kept, _ = sq.validate_candidates(CANDIDATES, sq.load_squads())
sim = tournament.simulate(gteams, gmk, allg, em, brk, sims=4000, seed=0)
pwin = blend_champion_probs(sim["win"], blended_probs()); champ = max(pwin, key=pwin.get)
sl = {(a, b): (s.home, s.away) for g in gr.values() for (a, b), s in zip(g.matches, g.scorelines)}
our = {"scorelines": sl, "champion": champ}
sc = {k: [((s.home, s.away), allg[k].exact(s.home, s.away)) for s in topk_scorelines(allg[k])] for k in allg}
ts_field = [(c, fame_score(c, tf)) for c in kept]
worlds = pool.sample_worlds(gteams, gmk, allg, em, brk, kept, tf, sims=6000, seed=1)
field = fld.generate_field(31, sc, pwin, ts_field, config.FIELD_SHARPNESS, np.random.default_rng(2))
def pwin_of(ts6):
    e = dict(our, topscorers=ts6)
    bw, rb, rc, cw = pool.score_field(e, field, worlds, gteams, gmk)
    return pool.champion_win_probs(bw, rb, rc, cw, [champ])[champ]
base = pick_topscorers(tf, n=6, risk="balanced", candidates=kept)
eng, _ = pool.pool_win_topscorers(dict(our, champion=champ), champ, kept, gteams, gmk, allg, em, brk,
                                  tf, pwin, sc, ts_field, 32, seed=1, sims=6000)
print("baseline (EV+reserve):", [c["name"] for c in base], "pool-win", round(pwin_of(base), 4))
print("engine  (pool-win)   :", [c["name"] for c in eng], "pool-win", round(pwin_of(eng), 4))
PY
```
Expected: engine pool-win ≥ baseline (within MC noise). If lower, the fame bias is too weak to exploit — document and switch the main path back to `pick_topscorers`.
- [ ] **Step 3: Write the finding** — create `docs/topscorer-ownership-calibration-2026-06-09.md` with the two pick lists + pool-win numbers from Step 2 and the verdict (real edge vs wash), mirroring the scoreline calibration doc.
- [ ] **Step 4: README** — under the model description note topscorers are engine-selected for pool-win against a fame-biased field (exploiting attacker over-ownership), linking the finding.
- [ ] **Step 5: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 6: Commit** `git add docs/topscorer-ownership-calibration-2026-06-09.md README.md && git commit -m "docs: topscorer-ownership calibration finding + README"`

---

## Self-Review

- **Spec coverage:** fame field §3 → Task 1 (+ field test Task 4); greedy core §4 → Task 2; wrapper §4 → Task 3; integration/risk §5 → Task 4; validation §6 → Task 5; config/error §7 (no new const, -inf fallback) → Task 2/3; testing §8 → Tasks 1-2,4,5. Covered.
- **Placeholder scan:** none — complete code + a runnable diagnostic.
- **Type consistency:** `fame_score(c, team_factors)` used identically in Tasks 1/4/5; `greedy_topscorers(our_fixed, max_rival, points_by_name, n_slots) -> (names, pwin)` matches its caller in `pool_win_topscorers`; `pool_win_topscorers(...) -> (picks, pool_win)` matches the `main` call (Task 4 Step 5) and diagnostic (Task 5); `ts_field_pool` (fame) replaces `ts_pool` everywhere it's passed; `ts_pool_win` initialized (Task 4 Step 3), set (Step 5), read in meta (Step 6) and report (Step 7).
- **Open risk:** champion is chosen under the EV-baseline topscorers, then topscorers under that champion (no iteration) — documented, additively near-separable. If Step 2 shows no uplift, Task 5 documents it and we keep `pick_topscorers` on the main path (one-line revert of Task 4 Step 5's `if` body).
