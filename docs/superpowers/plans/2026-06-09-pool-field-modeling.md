# Pool/field modeling — Implementation Plan (champion slice)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the champion `leverage`/`est_shares` heuristic with a principled choice that maximizes **P(our entry finishes 1st in the pool)**, via a reusable field model + nested-Monte-Carlo evaluator.

**Architecture:** `field.py` samples chalk-weighted rival entries. `pool.py` samples tournament *worlds* (reusing the goals grids + the `tournament` bracket helpers), scores every entry with `eval/metrics`, and a pure-math core (`champion_win_probs`) sweeps candidate champions over cached per-world arrays. `main` wires it in and sensitivity-checks the field sharpness.

**Tech Stack:** Python 3.12, numpy, penaltyblog (existing), pytest. No new deps.

---

## Task 1: per-world player goals (`topscorers.sample_player_goals`)

**Files:**
- Modify: `scorito/model/topscorers.py`
- Test: `tests/test_topscorers.py`

- [ ] **Step 1: Add the failing test**

```python
# append to tests/test_topscorers.py
import numpy as np
from scorito.model.topscorers import sample_player_goals


def test_sample_player_goals_mean_scales_with_rate_and_factor():
    cands = [dict(name="Striker", team="X", position="ATT", g90=0.6, start_prob=1.0, pen_taker=False),
             dict(name="Defender", team="X", position="DEF", g90=0.05, start_prob=1.0, pen_taker=False)]
    rng = np.random.default_rng(0)
    goals = sample_player_goals(cands, {"X": 1.0}, sims=20000, rng=rng)
    # lambda = g90*3*start (+0); striker ~1.8, defender ~0.15 over the 3 group games
    assert 1.6 < goals["Striker"].mean() < 2.0
    assert 0.05 < goals["Defender"].mean() < 0.25
    assert goals["Striker"].shape == (20000,)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_topscorers.py::test_sample_player_goals_mean_scales_with_rate_and_factor -q`
Expected: FAIL (`AttributeError: sample_player_goals`).

- [ ] **Step 3: Implement** (append to `scorito/model/topscorers.py`; add `import numpy as np` at the top with the other imports)

```python
def sample_player_goals(candidates, team_factors, sims, rng):
    """Per-world group-stage goals for each candidate ~ Poisson(lambda), with
    lambda = (g90*3*start_prob + PEN_BONUS*pen_share) * team_factor — consistent with the
    topscorer EV model. Returns {name: np.ndarray(sims)}."""
    out = {}
    for c in candidates:
        pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
        exp = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
        lam = max(0.0, exp * team_factors.get(c["team"], 1.0))
        out[c["name"]] = rng.poisson(lam, size=sims)
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_topscorers.py -q`
Expected: PASS (all topscorer tests).

- [ ] **Step 5: Commit**

```bash
git add scorito/model/topscorers.py tests/test_topscorers.py
git commit -m "feat(pool): per-world player-goal sampler for topscorer scoring"
```

## Task 2: field model (`field.generate_field`)

**Files:**
- Create: `scorito/model/field.py`
- Test: `tests/test_field.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_field.py
import numpy as np
from scorito.model import field as fld


def _inputs():
    champion_probs = {"Fav": 0.5, "Mid": 0.3, "Long": 0.2}
    scoreline_choices = {("A", "B"): [((1, 0), 0.6), ((2, 1), 0.3), ((0, 0), 0.1)]}
    topscorer_pool = [(dict(name=f"P{i}", team="A", position="ATT"), ev)
                      for i, ev in enumerate([30, 20, 15, 10, 8, 6, 4, 2])]
    return champion_probs, scoreline_choices, topscorer_pool


def test_chalky_field_concentrates_on_favourite():
    cp, sc, ts = _inputs()
    rng = np.random.default_rng(0)
    entries = fld.generate_field(400, sc, cp, ts, sharpness=3.0, rng=rng)
    assert len(entries) == 400
    champs = [e["champion"] for e in entries]
    # chalky -> Fav picked far more than its raw 0.5 share
    assert champs.count("Fav") / 400 > 0.6
    e = entries[0]
    assert set(e) == {"scorelines", "champion", "topscorers"}
    assert e["scorelines"][("A", "B")] in [(1, 0), (2, 1), (0, 0)]
    assert len(e["topscorers"]) == 6 and len({t["name"] for t in e["topscorers"]}) == 6


def test_sharpness_zero_is_near_uniform_champion():
    cp, sc, ts = _inputs()
    rng = np.random.default_rng(1)
    entries = fld.generate_field(600, sc, cp, ts, sharpness=0.0, rng=rng)
    share = [e["champion"] for e in entries].count("Fav") / 600
    assert 0.25 < share < 0.40   # ~1/3 uniform across the 3 teams


def test_field_is_seed_deterministic():
    cp, sc, ts = _inputs()
    a = fld.generate_field(50, sc, cp, ts, 2.0, np.random.default_rng(7))
    b = fld.generate_field(50, sc, cp, ts, 2.0, np.random.default_rng(7))
    assert [e["champion"] for e in a] == [e["champion"] for e in b]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_field.py -q`
Expected: FAIL (`ModuleNotFoundError: scorito.model.field`).

- [ ] **Step 3: Implement**

```python
# scorito/model/field.py
"""Generate plausible rival pool entries by sampling each pick from chalk-weighted
distributions. One ``sharpness`` exponent controls chalkiness (0 = ~uniform, higher =
piles onto favourites/modal scores). No pool data exists -> this is an explicit, tunable
assumption."""
import numpy as np


def _sharp_probs(weights, sharpness):
    w = np.asarray(weights, dtype=float) ** sharpness
    s = w.sum()
    return w / s if s > 0 else np.full(len(w), 1.0 / len(w))


def generate_field(n, scoreline_choices, champion_probs, topscorer_pool, sharpness, rng):
    """``scoreline_choices``: {(home,away): [(scoreline, exact_prob), ...]}.
    ``champion_probs``: {team: P(win)}. ``topscorer_pool``: [(candidate_dict, ev), ...].
    Returns a list of ``n`` entries {scorelines, champion, topscorers}."""
    teams = list(champion_probs)
    champ_p = _sharp_probs([champion_probs[t] for t in teams], sharpness)
    ts_cands = [c for c, _ in topscorer_pool]
    ts_p = _sharp_probs([ev for _, ev in topscorer_pool], sharpness)
    match_opts = {k: ([s for s, _ in v], _sharp_probs([p for _, p in v], sharpness))
                  for k, v in scoreline_choices.items()}

    entries = []
    for _ in range(n):
        scorelines = {}
        for k, (opts, p) in match_opts.items():
            scorelines[k] = opts[rng.choice(len(opts), p=p)]
        champion = teams[rng.choice(len(teams), p=champ_p)]
        idxs = rng.choice(len(ts_cands), size=6, replace=False, p=ts_p)
        topscorers = [ts_cands[i] for i in idxs]
        entries.append(dict(scorelines=scorelines, champion=champion, topscorers=topscorers))
    return entries
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_field.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/field.py tests/test_field.py
git commit -m "feat(pool): chalk-weighted field model (rival entry generator)"
```

## Task 3: world sampler (`pool.sample_worlds`)

**Files:**
- Create: `scorito/model/pool.py`
- Test: `tests/test_pool.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pool.py
import itertools

import numpy as np

from scorito.model import pool
from scorito.model.bracket import load_bracket
from scorito.model.grid import build_grid


def _world_inputs(sims=200):
    groups = "ABCDEFGHIJKL"
    gteams = {g: [f"{g}{i}" for i in range(1, 5)] for g in groups}
    even = build_grid(1.3, 1.1)
    group_matches, grids = [], {}
    for g in groups:
        for a, b in itertools.combinations(gteams[g], 2):
            group_matches.append((a, b))
            grids[(a, b)] = even
    elo = {f"{g}{i}": 1500.0 for g in groups for i in range(1, 5)}
    cands = [dict(name="A1", team="A1", position="ATT", g90=0.6, start_prob=1.0, pen_taker=False)]
    bracket = load_bracket("data/cache/worldcup2026.json")
    return gteams, group_matches, grids, elo, bracket, cands


def test_sample_worlds_shape_and_content():
    gteams, gm, grids, elo, bracket, cands = _world_inputs()
    worlds = pool.sample_worlds(gteams, gm, grids, elo, bracket, cands,
                                team_factors={}, sims=200, seed=0)
    assert len(worlds) == 200
    w = worlds[0]
    assert set(w) == {"scores", "place", "champion", "pgoals"}
    assert len(w["scores"]) == 72 and len(w["place"]) == 12
    assert w["champion"] in {f"{g}{i}" for g in gteams for i in range(1, 5)}
    assert w["pgoals"]["A1"] >= 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_pool.py::test_sample_worlds_shape_and_content -q`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# scorito/model/pool.py
"""Pool-win engine: sample tournament worlds, score entries, and choose the champion that
maximizes P(our entry finishes strictly 1st) against a modelled field. Reuses the goals
grids, the tournament bracket helpers, and eval/metrics."""
import numpy as np

from scorito import config
from scorito.eval.metrics import match_points, standings_points, topscorer_points
from scorito.model.bracket import ThirdSlot, assign_thirds, qualify_thirds
from scorito.model.group_sim import _award, _rank_table, _sample_scores
from scorito.model.topscorers import sample_player_goals
from scorito.model.tournament import ROUND_NEXT, _resolve, advance_matrix


def _grp_matches(gteams, group_matches):
    out = {g: [] for g in gteams}
    for (a, b) in group_matches:
        for g, ts in gteams.items():
            if a in ts and b in ts:
                out[g].append((a, b))
                break
    return out


def sample_worlds(gteams, group_matches, grids, elo, bracket, candidates,
                  team_factors, sims=config.POOL_WIN_SIMS, seed=0):
    """List of ``sims`` worlds: {scores:{(a,b):(h,a)}, place:{group:[teams]}, champion, pgoals:{name:int}}."""
    rng = np.random.default_rng(seed)
    all_teams = sorted({t for ts in gteams.values() for t in ts})
    P = advance_matrix(all_teams, elo)
    sampled = _sample_scores(group_matches, grids, sims, rng)
    pgoals = sample_player_goals(candidates, team_factors, sims, rng)
    grp = _grp_matches(gteams, group_matches)
    slot_locs = [(m.num, side, ref.allowed) for m in bracket
                 for side, ref in (("t1", m.team1), ("t2", m.team2)) if isinstance(ref, ThirdSlot)]

    worlds = []
    for s in range(sims):
        scores = {k: (int(sampled[k][0][s]), int(sampled[k][1][s])) for k in group_matches}
        place, thirds = {}, []
        for g, ts in gteams.items():
            stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
            h2h = {}
            for (a, b) in grp[g]:
                ga, gb = scores[(a, b)]
                h2h[(a, b)] = (ga, gb)
                _award(stats[a], stats[b], ga, gb)
            order = _rank_table(stats, h2h=h2h, rng=rng)
            place[g] = order
            if len(order) >= 3:
                thirds.append(dict(team=order[2], group=g, **stats[order[2]]))
        slot_team = {}
        if slot_locs:
            assigned = assign_thirds(qualify_thirds(thirds), [a for (_, _, a) in slot_locs])
            for j, (num, side, _) in enumerate(slot_locs):
                if j in assigned:
                    slot_team[(num, side)] = assigned[j]["team"]
        winners, losers = {}, {}
        champion = None
        for m in bracket:
            t1 = _resolve(m.team1, place, slot_team, winners, losers, m.num, "t1")
            t2 = _resolve(m.team2, place, slot_team, winners, losers, m.num, "t2")
            w_, l_ = (t1, t2) if rng.random() < P[(t1, t2)] else (t2, t1)
            winners[m.num], losers[m.num] = w_, l_
            if m.round == "Final":
                champion = w_
        worlds.append(dict(scores=scores, place=place, champion=champion,
                           pgoals={n: int(pgoals[n][s]) for n in pgoals}))
    return worlds
```

> NOTE: this mirrors `tournament.simulate`'s per-world body but also returns the scores/tables
> needed to score entries. (A later refactor could share one helper; kept separate here to avoid
> touching tested `tournament` code.)

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_pool.py::test_sample_worlds_shape_and_content -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/pool.py tests/test_pool.py
git commit -m "feat(pool): tournament world sampler (scores/tables/champion/goals)"
```

## Task 4: scoring + champion win-probability core (`pool`)

**Files:**
- Modify: `scorito/model/pool.py`
- Test: `tests/test_pool.py`

- [ ] **Step 1: Add failing tests** (the pure-math core is the crux — test it on hand arrays)

```python
# append to tests/test_pool.py
def test_champion_win_probs_no_field_is_one():
    probs = pool.champion_win_probs(np.zeros(10), np.zeros((0, 10)),
                                    [], np.array(["X"] * 10, dtype=object), ["X"])
    assert probs["X"] == 1.0


def test_champion_win_probs_brute_equivalence():
    rng = np.random.default_rng(0)
    W, N = 500, 4
    champ_w = np.array(rng.choice(["X", "Y"], W), dtype=object)
    base_w = rng.normal(1000, 10, W)
    rival_base = rng.normal(1000, 10, (N, W))
    rival_champ = ["X", "Y", "X", "Y"]
    fast = pool.champion_win_probs(base_w, rival_base, rival_champ, champ_w, ["X", "Y"])
    # brute: recompute P(win) for c="Y" by an explicit per-world loop
    wins = 0
    for w in range(W):
        ours = base_w[w] + 250 * (champ_w[w] == "Y")
        rivals = [rival_base[r, w] + 250 * (rival_champ[r] == champ_w[w]) for r in range(N)]
        wins += ours > max(rivals)
    assert abs(fast["Y"] - wins / W) < 1e-9


def test_champion_win_probs_leverage_off_overowned_favourite():
    # whole field on favourite X; X is champion 60% of worlds, Y 40%; bases ~equal.
    rng = np.random.default_rng(0)
    W, N = 4000, 25
    champ_w = np.where(rng.random(W) < 0.6, "X", "Y").astype(object)
    base_w = rng.normal(1000, 5, W)
    rival_base = rng.normal(1000, 5, (N, W))
    rival_champ = ["X"] * N
    probs = pool.champion_win_probs(base_w, rival_base, rival_champ, champ_w, ["X", "Y"])
    assert probs["Y"] > probs["X"]                  # core thesis: leverage off the crowd
    assert 0 <= probs["X"] <= 1 and 0 <= probs["Y"] <= 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_pool.py -q`
Expected: FAIL (`AttributeError: champion_win_probs`).

- [ ] **Step 3: Implement** (append to `scorito/model/pool.py`)

```python
def predicted_tables(entry, gteams, grp_matches):
    """Standings each group implies from this entry's scorelines (Scorito derives the table
    from your scores)."""
    tables = {}
    for g, ts in gteams.items():
        stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
        h2h = {}
        for (a, b) in grp_matches[g]:
            ga, gb = entry["scorelines"][(a, b)]
            h2h[(a, b)] = (ga, gb)
            _award(stats[a], stats[b], ga, gb)
        tables[g] = _rank_table(stats, h2h=h2h, rng=None)
    return tables


def _entry_base(entry, pred_tables, world):
    """Non-champion points for one entry in one world (scorelines + standings + topscorers)."""
    pts = sum(match_points(entry["scorelines"][k], world["scores"][k]) for k in world["scores"]
              if k in entry["scorelines"])
    pts += sum(standings_points(pred_tables[g], world["place"][g]) for g in world["place"])
    pts += topscorer_points(entry["topscorers"], world["pgoals"])
    return pts


def score_field(our_entry, field, worlds, gteams, group_matches):
    """Returns (base_w[W], rival_base[N,W], rival_champ[N], champ_w[W])."""
    grp = _grp_matches(gteams, group_matches)
    W = len(worlds)
    our_pred = predicted_tables(our_entry, gteams, grp)
    base_w = np.array([_entry_base(our_entry, our_pred, w) for w in worlds], dtype=float)
    rival_base = np.zeros((len(field), W))
    for r, e in enumerate(field):
        rp = predicted_tables(e, gteams, grp)
        rival_base[r] = [_entry_base(e, rp, w) for w in worlds]
    rival_champ = [e["champion"] for e in field]
    champ_w = np.array([w["champion"] for w in worlds], dtype=object)
    return base_w, rival_base, rival_champ, champ_w


def champion_win_probs(base_w, rival_base, rival_champ, champ_w, candidates,
                       bonus=config.CHAMPION_BONUS):
    """P(our entry finishes strictly 1st) for each candidate champion, holding our other picks
    fixed. ``base_w`` is our non-champion score per world; the field is fixed."""
    if rival_base.shape[0] == 0:
        return {c: 1.0 for c in candidates}
    rc = np.array(rival_champ, dtype=object)[:, None]
    rival_total = rival_base + bonus * (rc == champ_w[None, :])
    max_rival = rival_total.max(axis=0)
    return {c: float(np.mean(base_w + bonus * (champ_w == c) > max_rival)) for c in candidates}
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_pool.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/pool.py tests/test_pool.py
git commit -m "feat(pool): entry scoring + champion win-probability core (with leverage test)"
```

## Task 5: config + wire into `main` + `report`

**Files:**
- Modify: `scorito/config.py`, `scorito/main.py`, `scorito/report.py`
- Test: `tests/test_main_smoke.py`

- [ ] **Step 1: Add config knobs** — in `scorito/config.py` after `CHAMPION_MARKET_WEIGHT`:

```python
# Pool-win (field) model.
FIELD_SHARPNESS = 2.0      # chalkiness exponent (1 = pick ~ true prob; higher = chalkier)
POOL_WIN_SIMS = 5000       # tournament "worlds" sampled for the pool-win evaluator
```

- [ ] **Step 2: Add a `pool_win_champion` helper to `scorito/model/pool.py`** (assembles inputs, runs the field + worlds + sweep, with the sharpness sensitivity check)

```python
def pool_win_champion(our_entry, gteams, group_matches, grids, elo, bracket, candidates,
                      team_factors, champion_probs, scoreline_choices, topscorer_pool,
                      pool_size, candidate_champions, seed=0,
                      sims=config.POOL_WIN_SIMS, sharpnesses=(1.5, 2.0, 3.0)):
    """Returns (best_champion, {champion: P(win) at default sharpness}, stable: bool).
    Sensitivity-checked across ``sharpnesses``; ``stable`` is True iff the argmax agrees."""
    worlds = sample_worlds(gteams, group_matches, grids, elo, bracket, candidates,
                           team_factors, sims=sims, seed=seed)
    argmaxes, default_probs = [], None
    for sh in sharpnesses:
        field = generate_field(max(0, pool_size - 1), scoreline_choices, champion_probs,
                               topscorer_pool, sh, np.random.default_rng(seed + 1))
        base_w, rival_base, rival_champ, champ_w = score_field(
            our_entry, field, worlds, gteams, group_matches)
        probs = champion_win_probs(base_w, rival_base, rival_champ, champ_w, candidate_champions)
        argmaxes.append(max(probs, key=probs.get))
        if abs(sh - config.FIELD_SHARPNESS) < 1e-9:
            default_probs = probs
    if default_probs is None:                       # default not in the sweep -> compute it
        field = generate_field(max(0, pool_size - 1), scoreline_choices, champion_probs,
                               topscorer_pool, config.FIELD_SHARPNESS, np.random.default_rng(seed + 1))
        base_w, rival_base, rival_champ, champ_w = score_field(
            our_entry, field, worlds, gteams, group_matches)
        default_probs = champion_win_probs(base_w, rival_base, rival_champ, champ_w, candidate_champions)
    stable = len(set(argmaxes)) == 1
    best = max(default_probs, key=default_probs.get)
    return best, default_probs, stable
```

Add the imports it needs at the top of `pool.py`:
```python
from scorito.model.field import generate_field
```

- [ ] **Step 3: Wire it into `scorito/main.py`** — after the existing champion block (which computes `pwin`, `advance`, and `recommend_champion`). Replace the champion recommendation so the *pick* comes from the pool-win optimum when the full bracket is present:

```python
    pool_win = {}
    if len(gteams) == 12:
        from scorito.model import pool
        from scorito.model.match_ev import topk_scorelines
        from scorito.model.topscorers import score_candidate
        our_entry = {
            "scorelines": {(a, b): (s.home, s.away)
                           for g in group_results.values()
                           for (a, b), s in zip(g.matches, g.scorelines)},
            "champion": champion[0].team,
            "topscorers": result_topscorers,   # the pick_topscorers output (see below)
        }
        scoreline_choices = {k: [((s.home, s.away), all_grids[k].exact(s.home, s.away))
                                 for s in topk_scorelines(all_grids[k], k=config.TOPK_SCORELINES)]
                             for k in all_grids}
        ts_pool = [(c, score_candidate(c, team_factors)) for c in kept]
        contenders = [t for t, p in pwin.items() if p >= 0.02] or list(pwin)
        best, pool_win, stable = pool.pool_win_champion(
            our_entry, gteams, group_match_keys, all_grids, elo_map, brk, kept,
            team_factors, pwin, scoreline_choices, ts_pool, pool_size, contenders, seed=seed)
        # re-sort champion recs to put the pool-win pick first, annotate P(win-pool)
        champion = sorted(champion, key=lambda r: (r.team != best, -pool_win.get(r.team, 0.0)))
```

(Compute `result_topscorers = pick_topscorers(...)` once into a variable *before* building `our_entry`, and pass that same variable to `RunResult`. Add `pool_win`/`stable` to `RunResult` via a new field `pool_win: dict = field(default_factory=dict)`.)

- [ ] **Step 4: Show it in `scorito/report.py`** — add `pool_win: dict = field(default_factory=dict)` to `RunResult`, and a `Win-pool` column to the champion table:

```python
    L.append("| Team | P(win) | Win-pool | EV | Share | Lev | R16 | QF | SF | Final |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in result.champion[:5]:
        a = result.advance.get(r.team, {})
        wp = result.pool_win.get(r.team)
        L.append(f"| {r.team} | {r.p_win:.1%} | {wp:.1%} | {r.ev_points:.0f} | {r.est_share:.0%} | "
                 f"{r.leverage:.4f} | {a.get('r16', 0):.0%} | {a.get('qf', 0):.0%} | "
                 f"{a.get('sf', 0):.0%} | {a.get('final', 0):.0%} |"
                 if wp is not None else
                 f"| {r.team} | {r.p_win:.1%} | – | {r.ev_points:.0f} | {r.est_share:.0%} | "
                 f"{r.leverage:.4f} | {a.get('r16', 0):.0%} | {a.get('qf', 0):.0%} | "
                 f"{a.get('sf', 0):.0%} | {a.get('final', 0):.0%} |")
```

Update the recommendation line below to name the pool-win pick and flag if `stable` is False (pass `result.meta["pool_win_stable"]`).

- [ ] **Step 5: Update the smoke test** `tests/test_main_smoke.py` — the 1-group sample skips the pool-win path (guarded by `len(gteams) == 12`), so add:

```python
    assert res.pool_win == {}   # 1-group sample -> pool-win guarded off
```

- [ ] **Step 6: Run the suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (all, incl. new field/pool/topscorer tests).

- [ ] **Step 7: Commit**

```bash
git add scorito/config.py scorito/model/pool.py scorito/main.py scorito/report.py tests/test_main_smoke.py
git commit -m "feat(pool): wire pool-win champion into run + Win-pool column"
```

## Task 6: real run, sensitivity, docs

**Files:**
- Modify: `README.md`
- (verification)

- [ ] **Step 1: Real run** — `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --pool-size 40 --risk balanced`
  Expected: completes (note runtime); champion table shows a `Win-pool` % column; sanity-check that the pool-win pick is *near-EV with selective leverage* (per the research it should NOT be wildly contrarian for a 40-person field) and that it's stable across the sharpness sweep. If the run is too slow, lower `POOL_WIN_SIMS`.

- [ ] **Step 2: README** — under the model description, note the champion is chosen to maximize **P(finish 1st in the pool)** via a field model + nested simulation (tunable `FIELD_SHARPNESS`), replacing the old leverage heuristic.

- [ ] **Step 3: Final suite** — `.venv/bin/python -m pytest -q` → all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: champion pick now maximizes P(win pool) via field model"
```

---

## Self-Review

- **Spec coverage:** field model §8 → Task 2; world sampler §7 → Task 3; player goals §7 → Task 1; scoring §6 + evaluator/optimizer §9 → Task 4; config §10 → Task 5; integration/report §11 → Task 5; sensitivity check §10 → Task 5 (`pool_win_champion` sweeps sharpness); testing §13 → Tasks 2,4 (leverage property in Task 4); perf §14 → Task 6.
- **Placeholder scan:** none — code complete. (Task 5 Step 3 references `result_topscorers`/`pool_win_champion` which it defines; `RunResult.pool_win` added in Step 4.)
- **Type consistency:** entry dict `{scorelines:{(a,b):(h,a)}, champion, topscorers}` consistent across `field`, `pool._entry_base`, `score_field`, and `main`'s `our_entry`. `champion_win_probs(base_w, rival_base, rival_champ, champ_w, candidates)` matches its callers and tests. `sample_worlds(...)->[{scores,place,champion,pgoals}]` consumed by `_entry_base`/`score_field`. `sample_player_goals(candidates, team_factors, sims, rng)` matches Task 1 + `sample_worlds`.
- **Open risk / perf:** `score_field` scores `N≈39` rivals × `W≈5000` worlds in Python (~tens of seconds); Task 6 Step 1 will reveal real timing and can drop `POOL_WIN_SIMS`. Player goals are sampled independently of exact team scorelines (documented approximation). The leverage effect requires a non-trivial field — covered by the `N=25` test, not a 1-rival case.
