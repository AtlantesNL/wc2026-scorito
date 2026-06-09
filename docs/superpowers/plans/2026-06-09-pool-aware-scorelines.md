# Pool-aware scorelines — Implementation Plan (Approach A)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Replace the per-match raw-EV scoreline objective (and retire `toto_weight`) with a pool-leverage-adjusted objective driven by a draw-averse field model, so the optimizer surgically predicts under-owned draws while staying near-chalk.

**Architecture:** A draw-averse `field.scoreline_ownership(grid)` gives per-match rival pick fractions; `match_ev` discounts each candidate's exact/toto points by that ownership (`L(own)=1/(1+own·(N−1))^γ`); `group_opt`/`main` pass it through; the existing pool-win evaluator validates the uplift.

**Tech Stack:** Python 3.12, numpy, pytest. No new deps.

---

## Task 1: config constants

**Files:** Modify `scorito/config.py`, `tests/test_config.py`

- [ ] **Step 1: Failing test** — append to `tests/test_config.py`:
```python
def test_scoreline_leverage_constants():
    assert 0 < config.DRAW_AVERSION < 1
    assert config.SCORELINE_LEVERAGE_GAMMA["max_ev"] == 0.0
    assert config.SCORELINE_LEVERAGE_GAMMA["aggressive"] > config.SCORELINE_LEVERAGE_GAMMA["balanced"] > 0
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_config.py::test_scoreline_leverage_constants -q` → FAIL (AttributeError).
- [ ] **Step 3: Implement** — in `scorito/config.py`, after the `POOL_WIN_SIMS` line add:
```python
# Pool-aware scorelines: amateur rivals avoid draws — they pick ~DRAW_AVERSION of the draws the
# model implies. SCORELINE_LEVERAGE_GAMMA discounts crowded outcomes (per risk); pool size enters
# via the leverage denominator (own·(N-1)), so small pools stay near-chalk automatically.
DRAW_AVERSION = 0.4
SCORELINE_LEVERAGE_GAMMA = {"max_ev": 0.0, "balanced": 0.5, "aggressive": 1.0}
```
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add scorito/config.py tests/test_config.py && git commit -m "feat(scorelines): config DRAW_AVERSION + SCORELINE_LEVERAGE_GAMMA"`

## Task 2: draw-averse field ownership model

**Files:** Modify `scorito/model/field.py`, `tests/test_field.py`

- [ ] **Step 1: Failing test** — append to `tests/test_field.py`:
```python
def test_scoreline_ownership_downweights_draws_and_sums_to_one():
    from scorito.model.grid import ScoreGrid
    from scorito.model.field import scoreline_ownership
    m = np.zeros((3, 3)); m[1, 0] = 0.4; m[1, 1] = 0.3; m[0, 0] = 0.1; m[2, 1] = 0.2
    g = ScoreGrid(m, p_home=0.6, p_draw=0.4, p_away=0.0)   # draws (1-1,0-0) = 0.4 of the grid
    oe, ot = scoreline_ownership(g, draw_aversion=0.4, sharpness=1.0)
    assert abs(sum(oe.values()) - 1.0) < 1e-9
    assert abs(ot["home"] + ot["draw"] + ot["away"] - 1.0) < 1e-9
    assert ot["draw"] < 0.4                                   # draws down-weighted below grid share
    oe2, ot2 = scoreline_ownership(g, draw_aversion=1.0, sharpness=1.0)
    assert abs(ot2["draw"] - 0.4) < 1e-9                      # aversion=1 -> raw grid share
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_field.py -q` → FAIL (AttributeError).
- [ ] **Step 3: Implement** — append to `scorito/model/field.py` (`numpy as np` already imported):
```python
def scoreline_ownership(grid, draw_aversion, sharpness):
    """Per-match rival pick distribution: the model grid with draw cells down-weighted (amateurs
    avoid draws), renormalized then sharpened. Returns (own_exact {(i,j): frac}, own_toto
    {"home"/"draw"/"away": frac}) — both summing to 1 (one rival's pick)."""
    n = grid.matrix.shape[0]
    cells = [(i, j) for i in range(n) for j in range(n)]
    w = np.array([grid.exact(i, j) * (draw_aversion if i == j else 1.0) for (i, j) in cells])
    w = w ** sharpness
    s = w.sum()
    w = w / s if s > 0 else np.full(len(w), 1.0 / len(w))
    own_exact = {cells[k]: float(w[k]) for k in range(len(cells))}
    own_toto = {"home": 0.0, "draw": 0.0, "away": 0.0}
    for (i, j), p in own_exact.items():
        own_toto["home" if i > j else "away" if j > i else "draw"] += p
    return own_exact, own_toto
```
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add scorito/model/field.py tests/test_field.py && git commit -m "feat(scorelines): draw-averse field ownership model"`

## Task 3: leverage-adjusted objective (match_ev + group_opt + main + report)

This is the coupled signature swap; raw-EV defaults keep untouched callers/tests green.

**Files:** Modify `scorito/model/match_ev.py`, `scorito/model/group_opt.py`, `scorito/main.py`, `scorito/report.py`, `tests/test_match_ev.py`

- [ ] **Step 1: Replace the failing `toto_weight` test** in `tests/test_match_ev.py` — replace `test_toto_weight_tilts_toward_exact_score` (the whole function) with:
```python
def test_leverage_tilts_toward_underowned_draw():
    g = _tilt_grid()                                  # 1-0 broad toto; 1-1 modal exact
    safe = topk_scorelines(g, k=1)[0]                 # no field -> raw EV
    assert (safe.home, safe.away) == (1, 0)
    # draw-averse field: the draw outcome is under-owned -> high leverage
    own_exact = {(1, 0): 0.4, (2, 0): 0.3, (1, 1): 0.05, (0, 1): 0.1}
    own_toto = {"home": 0.7, "draw": 0.05, "away": 0.1}
    bold = topk_scorelines(g, k=1, own_exact=own_exact, own_toto=own_toto,
                           n_rivals=30, gamma=0.5)[0]
    assert (bold.home, bold.away) == (1, 1)           # leverage chases the under-owned draw
    assert abs(bold.ev - score_ev(g, 1, 1, 1.0)) < 1e-9   # ev still = true EV
    assert bold.ev != bold.sel
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_match_ev.py -q` → FAIL (`topk_scorelines` has no `own_exact`).
- [ ] **Step 3a: Rewrite `scorito/model/match_ev.py`** to:
```python
"""Per-match Scorito points. ``ev`` = true expected points (45·P(exact)+30·P(toto)); ``sel`` =
the pool-leverage-adjusted selection score that discounts crowded outcomes by the field's
ownership of them (the per-match analog of the champion leverage)."""
from scorito import config
from scorito.types import Scoreline


def score_ev(grid, i, j, toto_weight=1.0):
    """True EV (toto_weight=1.0); toto_weight kept only so existing callers/tests still read EV."""
    if i > j:
        p_toto = grid.p_home
    elif j > i:
        p_toto = grid.p_away
    else:
        p_toto = grid.p_draw
    return config.PTS_EXACT * grid.exact(i, j) + config.PTS_TOTO * toto_weight * p_toto


def _leverage(own, n_rivals, gamma):
    """Discount for a crowded outcome: 1/(1+own*n_rivals)^gamma (own = rival pick fraction)."""
    return 1.0 / (1.0 + own * n_rivals) ** gamma


def score_sel(grid, i, j, own_exact, own_toto, n_rivals, gamma):
    """Leverage-adjusted selection score: exact + toto points, each discounted by ownership."""
    o = "home" if i > j else "away" if j > i else "draw"
    p_toto = {"home": grid.p_home, "away": grid.p_away, "draw": grid.p_draw}[o]
    ex = config.PTS_EXACT * grid.exact(i, j) * _leverage(own_exact.get((i, j), 0.0), n_rivals, gamma)
    to = config.PTS_TOTO * p_toto * _leverage(own_toto.get(o, 0.0), n_rivals, gamma)
    return ex + to


def topk_scorelines(grid, k=config.TOPK_SCORELINES, own_exact=None, own_toto=None,
                    n_rivals=0, gamma=0.0):
    """Top-k by the selection score ``sel``; each keeps its true ``ev`` for reporting. With no
    field (own_exact None, or gamma 0, or n_rivals 0) ``sel == ev`` (pure EV)."""
    n = grid.matrix.shape[0]
    use_lev = own_exact is not None and gamma > 0 and n_rivals > 0
    oe, ot = own_exact or {}, own_toto or {}
    cands = []
    for i in range(n):
        for j in range(n):
            ev = score_ev(grid, i, j, 1.0)
            sel = score_sel(grid, i, j, oe, ot, n_rivals, gamma) if use_lev else ev
            cands.append(Scoreline(i, j, ev=ev, sel=sel))
    cands.sort(key=lambda s: s.sel, reverse=True)
    return cands[:k]
```
- [ ] **Step 3b: Update `scorito/model/group_opt.py`** — change `optimize_group`'s signature line `sims=config.MC_SIMS, seed=0, probs=None, group="", toto_weight=1.0):` to:
```python
                   sims=config.MC_SIMS, seed=0, probs=None, group="",
                   own_by_match=None, n_rivals=0, gamma=0.0):
```
and the `cand = ...` line (currently `cand = [topk_scorelines(grids[m], k, toto_weight) for m in matches]`) to:
```python
    obm = own_by_match or {}
    cand = [topk_scorelines(grids[m], k, *obm.get(m, (None, None)), n_rivals, gamma)
            for m in matches]
```
- [ ] **Step 3c: Update `scorito/main.py`** — (i) add import near the other model imports: `from scorito.model import field`. (ii) Delete the line `toto_weight = config.scoreline_toto_weight(risk, pool_size)`. (iii) In the group loop, after `all_grids.update(grids)` add:
```python
        own_by_match = {key: field.scoreline_ownership(grids[key], config.DRAW_AVERSION,
                                                        config.FIELD_SHARPNESS) for key in grids}
```
and change the `optimize_group(...)` call from `..., group=g, toto_weight=toto_weight)` to:
```python
        group_results[g] = optimize_group(teams, gmatches, grids, k=k, sims=sims, seed=seed,
                                          group=g, own_by_match=own_by_match, n_rivals=pool_size - 1,
                                          gamma=config.SCORELINE_LEVERAGE_GAMMA.get(risk, 0.0))
```
(iv) In the `RunResult(...)` `meta=` dict, remove `"scoreline_toto_weight": toto_weight,` (keep `pool_win_stable`/`pool_win_sims`).
- [ ] **Step 3d: Update `scorito/report.py`** — replace the two lines computing `boldness`/`_Scoreline tilt:_` with:
```python
    n_draws = sum(1 for gr in result.groups.values() for s in gr.scorelines if s.home == s.away)
    n_sl = sum(len(gr.scorelines) for gr in result.groups.values())
    L.append(f"_Scorelines:_ pool-leverage-adjusted (draw-aware); {n_draws}/{n_sl} predicted draws\n")
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest -q` → PASS (test_match_ev flip + everything else; group_opt/main use raw-EV defaults where no field).
- [ ] **Step 5: Commit** `git add scorito/model/match_ev.py scorito/model/group_opt.py scorito/main.py scorito/report.py tests/test_match_ev.py && git commit -m "feat(scorelines): leverage-adjusted (draw-aware) scoreline objective"`

## Task 4: retire the dead toto_weight path

**Files:** Modify `scorito/config.py`, `tests/test_config.py`

- [ ] **Step 1:** In `scorito/config.py` delete the `SCORELINE_BOLDNESS = {...}` line, its comment block, and the entire `def scoreline_toto_weight(...)` function.
- [ ] **Step 2:** In `tests/test_config.py` delete `test_scoreline_toto_weight` (it referenced the removed function).
- [ ] **Step 3: Run** `.venv/bin/python -m pytest -q` → PASS (nothing references them after Task 3).
- [ ] **Step 4: Commit** `git add scorito/config.py tests/test_config.py && git commit -m "refactor(scorelines): retire superseded toto_weight/SCORELINE_BOLDNESS"`

## Task 5: real run, pool-win uplift evidence, README

**Files:** Modify `README.md`; verification

- [ ] **Step 1: Real run** — `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --risk balanced`. Expected: completes; report's scoreline line shows a **modest** number of predicted draws (single digits across 72, not draws-everywhere); spot-check that tight games picked draws and blowouts stayed favourite-wins.
- [ ] **Step 2: Pool-win uplift evidence** — run this diagnostic (reuses the pool evaluator to score our leverage entry vs an all-chalk entry, champion+topscorers equal):
```bash
.venv/bin/python - <<'PY'
import json
from collections import defaultdict
from scorito.data import elo, fixtures, odds as om, squads as sq
from scorito.data.fixtures import group_teams
from scorito.data.topscorer_candidates import CANDIDATES
from scorito import config
from scorito.model.goals import expected_goals
from scorito.model.grid import build_grid
from scorito.model.group_opt import optimize_group
from scorito.model import field, pool, tournament, bracket as bk
from scorito.model.topscorers import pick_topscorers, score_candidate
from scorito.data.priors import blended_probs, blend_champion_probs
from scorito.main import _default_fixtures
matches = fixtures.load_fixtures(_default_fixtures()); gteams = group_teams(matches)
ats = sorted({t for ts in gteams.values() for t in ts}); em = elo.get_elo(ats)
eg = dict(em)
for h in config.HOSTS:
    if h in eg: eg[h] += config.HOST_ELO_BONUS
omap = om.parse_odds(json.load(open("data/cache/odds_raw.json")))
allg = {}; gr_lev = {}; gr_chalk = {}
for g, ts in gteams.items():
    gm = [m for m in matches if m.group == g]; gmk = [(m.team1, m.team2) for m in gm]; grd = {}
    for m in gm:
        l1, l2 = expected_goals(m, omap, eg); grd[(m.team1, m.team2)] = build_grid(l1, l2)
    allg.update(grd)
    obm = {k: field.scoreline_ownership(grd[k], config.DRAW_AVERSION, config.FIELD_SHARPNESS) for k in grd}
    gr_lev[g] = optimize_group(ts, gmk, grd, k=config.TOPK_SCORELINES, sims=4000, seed=0, group=g,
                               own_by_match=obm, n_rivals=31, gamma=config.SCORELINE_LEVERAGE_GAMMA["balanced"])
    gr_chalk[g] = optimize_group(ts, gmk, grd, k=config.TOPK_SCORELINES, sims=4000, seed=0, group=g)
tl = defaultdict(list)
for m in matches:
    l1, l2 = expected_goals(m, omap, eg); tl[m.team1].append(l1); tl[m.team2].append(l2)
means = {t: sum(v)/len(v) for t, v in tl.items()}; avg = sum(means.values())/len(means); tf = {t: means[t]/avg for t in means}
brk = bk.load_bracket(_default_fixtures()); gmk = [(m.team1, m.team2) for m in matches]
kept, _ = sq.validate_candidates(CANDIDATES, sq.load_squads()); ts6 = pick_topscorers(tf, n=6, risk="balanced", candidates=kept)
sim = tournament.simulate(gteams, gmk, allg, em, brk, sims=4000, seed=0); pwin = blend_champion_probs(sim["win"], blended_probs())
champ = max(pwin, key=pwin.get)
def entry(grs): return {"scorelines": {(a, b): (s.home, s.away) for g in grs.values() for (a, b), s in zip(g.matches, g.scorelines)}, "champion": champ, "topscorers": ts6}
worlds = pool.sample_worlds(gteams, gmk, allg, em, brk, kept, tf, sims=6000, seed=1)
fld = field.generate_field(31, {k: [((s.home, s.away), allg[k].exact(s.home, s.away)) for s in __import__("scorito.model.match_ev", fromlist=["topk_scorelines"]).topk_scorelines(allg[k])] for k in allg}, pwin, [(c, score_candidate(c, tf)) for c in kept], config.FIELD_SHARPNESS, __import__("numpy").random.default_rng(2))
def pwin_of(e):
    bw, rb, rc, cw = pool.score_field(e, fld, worlds, gteams, gmk)
    return pool.champion_win_probs(bw, rb, rc, cw, [e["champion"]])[e["champion"]]
print("draws lev :", sum(1 for g in gr_lev.values() for s in g.scorelines if s.home == s.away))
print("draws chalk:", sum(1 for g in gr_chalk.values() for s in g.scorelines if s.home == s.away))
print("pool-win leverage:", round(pwin_of(entry(gr_lev)), 4), " chalk:", round(pwin_of(entry(gr_chalk)), 4))
PY
```
Expected: leverage entry predicts a few more draws and has **pool-win ≥ chalk** (within MC noise). If lower, reduce `SCORELINE_LEVERAGE_GAMMA["balanced"]` and re-run.
- [ ] **Step 3: README** — under the model description note scorelines are pool-leverage-adjusted (draw-aware), exploiting the field's draw-aversion, replacing the old boldness tilt.
- [ ] **Step 4: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 5: Commit** `git add README.md && git commit -m "docs: pool-aware (draw-exploiting) scorelines"`

---

## Self-Review

- **Spec coverage:** field model §3 → Task 2; leverage objective §4 → Task 3; integration §5 → Task 3; validation §6 → Task 5 Step 2; config §7 → Task 1 + Task 4 (retire); testing §9 → Tasks 1-3,5. All covered.
- **Placeholder scan:** none — complete code + a runnable diagnostic.
- **Type consistency:** `topk_scorelines(grid, k, own_exact, own_toto, n_rivals, gamma)` matches `group_opt` (`*obm.get(m,(None,None)), n_rivals, gamma`) and `test_match_ev`; `scoreline_ownership` returns `(own_exact, own_toto)` consumed as the tuple unpacked in `group_opt` and built in `main`; raw-EV default (`own_exact None`/`gamma 0`) preserves every existing `optimize_group`/`topk_scorelines` caller (group_opt tests pass `seed`/`k` only).
- **Open risk:** the objective mixes leverage-discounted scoreline `sel` with raw standings points (standings-leverage out of scope) — if draws over/under-fire, tune `SCORELINE_LEVERAGE_GAMMA["balanced"]`; Task 5 Step 2 is the guardrail (pool-win must not drop).
