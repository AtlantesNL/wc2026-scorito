# Champion full-tournament Monte-Carlo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static 11-team champion `P(win)` dict with a seeded full-tournament Monte-Carlo (all 48 teams, draw-aware), blended with the market/Opta prior, feeding the existing leverage layer.

**Architecture:** `bracket.py` parses the openfootball KO tree + does third-place constraint-matching (pure). `tournament.py` precomputes an Elo advance matrix then samples N tournaments (reusing `_sample_scores`/`_rank_table`) → `P(win)` + advancement. `priors.blend_champion_probs` blends MC with market; `champion.recommend_champion` now takes a probs dict; `main`/`report` wire it through.

**Tech Stack:** Python 3.12, numpy, scipy (`linear_sum_assignment`, already used), penaltyblog (existing), pytest. No new deps.

---

## Task 1: config + `blend_champion_probs`

**Files:**
- Modify: `scorito/config.py`
- Modify: `scorito/data/priors.py`
- Test: `tests/test_priors.py` (new)

- [ ] **Step 1: Add the config constant**

In `scorito/config.py`, after `CHAMPION_BONUS = 250` add:
```python
# Champion P(win): blend weight for the market/Opta prior vs the simulation backbone.
# 0.0 = pure Monte-Carlo, 1.0 = market-anchored.
CHAMPION_MARKET_WEIGHT = 0.5
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_priors.py
import pytest
from scorito.data.priors import blend_champion_probs


def test_blend_weight_zero_is_pure_mc():
    mc = {"A": 0.5, "B": 0.3, "C": 0.2}
    out = blend_champion_probs(mc, {"A": 0.9}, weight=0.0)
    assert out == pytest.approx(mc)


def test_blend_sums_to_one_and_pulls_toward_market():
    mc = {"A": 0.2, "B": 0.2, "C": 0.6}
    market = {"A": 0.5}                       # only A covered (sums 0.5 < 1)
    out = blend_champion_probs(mc, market, weight=1.0)  # market_full only
    assert sum(out.values()) == pytest.approx(1.0)
    # A gets its market prob; B,C split the 0.5 residual in proportion to mc (0.2:0.6)
    assert out["A"] == pytest.approx(0.5)
    assert out["B"] == pytest.approx(0.5 * 0.2 / 0.8)
    assert out["C"] == pytest.approx(0.5 * 0.6 / 0.8)


def test_blend_half_and_half_sums_to_one():
    mc = {"A": 0.2, "B": 0.2, "C": 0.6}
    out = blend_champion_probs(mc, {"A": 0.5}, weight=0.5)
    assert sum(out.values()) == pytest.approx(1.0)
    assert out["A"] == pytest.approx(0.5 * 0.5 + 0.5 * 0.2)
```

- [ ] **Step 3: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_priors.py -q`
Expected: FAIL (`ImportError: cannot import name 'blend_champion_probs'`).

- [ ] **Step 4: Implement (append to `scorito/data/priors.py`)**

```python
def blend_champion_probs(mc, market, weight=None):
    """Blend the simulation's P(win) (``mc``, all teams, the backbone) with the market/Opta
    prior (``market``, a few teams). The market is extended to all teams by spreading its
    residual mass over the uncovered teams in proportion to ``mc``; then
    ``out = weight*market_full + (1-weight)*mc`` (sums to 1)."""
    from scorito import config
    w = config.CHAMPION_MARKET_WEIGHT if weight is None else weight
    covered = {t: market[t] for t in market if t in mc}
    s = sum(covered.values())
    market_full = dict(covered)
    uncovered = [t for t in mc if t not in covered]
    if s >= 1.0:
        market_full = {t: p / s for t, p in covered.items()}
        for t in uncovered:
            market_full[t] = 0.0
    else:
        denom = sum(mc[t] for t in uncovered) or 1.0
        for t in uncovered:
            market_full[t] = (1.0 - s) * mc[t] / denom
    return {t: w * market_full.get(t, 0.0) + (1.0 - w) * mc[t] for t in mc}
```

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_priors.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scorito/config.py scorito/data/priors.py tests/test_priors.py
git commit -m "feat(champion): config weight + blend_champion_probs (MC x market)"
```

## Task 2: `recommend_champion` takes a probs dict

**Files:**
- Modify: `scorito/model/champion.py`
- Modify: `tests/test_champion.py`

- [ ] **Step 1: Update the failing test** to the new signature

Replace the entire contents of `tests/test_champion.py` with:
```python
from scorito.model.champion import recommend_champion

# A fixed P(win) dict so these tests exercise only the leverage layer.
PWIN = {"Spain": 0.18, "France": 0.15, "Brazil": 0.12, "England": 0.10,
        "Argentina": 0.09, "Germany": 0.06, "Netherlands": 0.05}


def test_ev_points_is_p_times_bonus():
    recs = {r.team: r for r in recommend_champion(PWIN, pool_size=40, risk="balanced")}
    assert abs(recs["Spain"].ev_points - PWIN["Spain"] * 250) < 1e-9


def test_larger_pool_pushes_off_the_consensus_favorite():
    def rank_of(recs, team):
        return [r.team for r in recs].index(team)
    small = recommend_champion(PWIN, pool_size=8, risk="balanced")
    large = recommend_champion(PWIN, pool_size=400, risk="balanced")
    assert rank_of(large, "Spain") >= rank_of(small, "Spain")


def test_max_ev_ranks_by_pure_win_prob():
    recs = recommend_champion(PWIN, pool_size=100, risk="max_ev")
    pwins = [r.p_win for r in recs]
    assert pwins == sorted(pwins, reverse=True)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_champion.py -q`
Expected: FAIL (`recommend_champion()` got an unexpected/positional `pwin`, or uses internal dict).

- [ ] **Step 3: Implement** — edit `scorito/model/champion.py`

Remove the import `from scorito.data.priors import blended_probs` (no longer used here). Replace `recommend_champion` with:
```python
def recommend_champion(pwin, pool_size, risk="balanced"):
    """Return ChampionRecs sorted by pool-adjusted leverage (best first).

    ``pwin``: ``{team: P(win)}`` (e.g. the blended simulation+market probabilities)."""
    shares = est_shares(pwin)
    recs = [
        ChampionRec(
            team=t,
            p_win=p,
            ev_points=p * config.CHAMPION_BONUS,
            est_share=shares[t],
            leverage=leverage_score(p, shares[t], pool_size, risk),
        )
        for t, p in pwin.items()
    ]
    recs.sort(key=lambda r: r.leverage, reverse=True)
    return recs
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_champion.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/champion.py tests/test_champion.py
git commit -m "refactor(champion): recommend_champion takes an explicit P(win) dict"
```

## Task 3: `bracket.py` — parse the KO tree

**Files:**
- Create: `scorito/model/bracket.py`
- Test: `tests/test_bracket.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bracket.py
from scorito.model import bracket as bk


def test_parse_refs():
    assert bk._parse_ref("1A") == bk.GroupPos(1, "A")
    assert bk._parse_ref("2B") == bk.GroupPos(2, "B")
    assert bk._parse_ref("3A/B/C/D/F") == bk.ThirdSlot(frozenset("ABCDF"))
    assert bk._parse_ref("W74") == bk.WinnerOf(74)
    assert bk._parse_ref("L101") == bk.LoserOf(101)


def test_parse_ref_rejects_garbage():
    import pytest
    with pytest.raises(ValueError):
        bk._parse_ref("XYZ")


def test_load_bracket_real_fixture():
    b = bk.load_bracket("data/cache/worldcup2026.json")
    assert len(b) == 32                       # 16+8+4+2+1+1
    rounds = {m.round for m in b}
    assert "Round of 32" in rounds and "Final" in rounds
    r32 = [m for m in b if m.round == "Round of 32"]
    assert len(r32) == 16
    thirds = [r for m in b for r in (m.team1, m.team2) if isinstance(r, bk.ThirdSlot)]
    assert len(thirds) == 8                   # eight third-place slots in R32
    final = [m for m in b if m.round == "Final"][0]
    assert isinstance(final.team1, bk.WinnerOf) and isinstance(final.team2, bk.WinnerOf)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_bracket.py -q`
Expected: FAIL (`ModuleNotFoundError: scorito.model.bracket`).

- [ ] **Step 3: Implement**

```python
# scorito/model/bracket.py
"""Parse the openfootball knockout tree into typed references + third-place matching.

Pure structure/assignment logic (no randomness except an optional rng for third-place
ranking ties). Token grammar in the fixtures file:
  "1A"/"2B"   -> GroupPos(pos, group)
  "3A/B/C/D/F"-> ThirdSlot(allowed groups)      (eight such slots in the Round of 32)
  "W74"/"L101"-> WinnerOf / LoserOf match number
The Final ("W101 vs W102") and third-place playoff ("L101 vs L102") have num=None in the
source; we assign them synthetic numbers > all real ones so they sort last.
"""
import json
import re
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class GroupPos:
    pos: int
    group: str


@dataclass(frozen=True)
class ThirdSlot:
    allowed: frozenset


@dataclass(frozen=True)
class WinnerOf:
    num: int


@dataclass(frozen=True)
class LoserOf:
    num: int


@dataclass
class KOMatch:
    num: int
    round: str
    team1: object
    team2: object


def _parse_ref(tok):
    tok = str(tok).strip()
    m = re.fullmatch(r"([12])([A-L])", tok)
    if m:
        return GroupPos(int(m.group(1)), m.group(2))
    m = re.fullmatch(r"3([A-L](?:/[A-L])*)", tok)
    if m:
        return ThirdSlot(frozenset(m.group(1).split("/")))
    m = re.fullmatch(r"W(\d+)", tok)
    if m:
        return WinnerOf(int(m.group(1)))
    m = re.fullmatch(r"L(\d+)", tok)
    if m:
        return LoserOf(int(m.group(1)))
    raise ValueError(f"Unparseable bracket token: {tok!r}")


def load_bracket(fixtures_src):
    """Return the 32 knockout matches as KOMatch nodes, ordered by num."""
    if str(fixtures_src).startswith("http"):
        data = requests.get(fixtures_src, timeout=30).json()
    else:
        with open(fixtures_src, encoding="utf-8") as f:
            data = json.load(f)
    ko = [m for m in data["matches"] if not m.get("group")]
    out, synth = [], 10_000
    for m in ko:
        num = m.get("num")
        if num is None:
            num = synth
            synth += 1
        out.append(KOMatch(num=num, round=m["round"],
                           team1=_parse_ref(m["team1"]), team2=_parse_ref(m["team2"])))
    out.sort(key=lambda x: x.num)
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_bracket.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/bracket.py tests/test_bracket.py
git commit -m "feat(bracket): parse openfootball knockout tree into typed refs"
```

## Task 4: third-place qualification + constraint matching

**Files:**
- Modify: `scorito/model/bracket.py`
- Test: `tests/test_bracket.py`

- [ ] **Step 1: Add failing tests**

```python
# append to tests/test_bracket.py
def test_qualify_thirds_takes_best_eight_by_pts_gd_gf():
    thirds = [dict(team=f"T{i}", group="ABCDEFGHIJKL"[i],
                   pts=i, gd=0, gf=0) for i in range(12)]
    q = bk.qualify_thirds(thirds)
    assert len(q) == 8
    assert {t["team"] for t in q} == {f"T{i}" for i in range(4, 12)}  # top 8 by pts


def test_assign_thirds_respects_allowed_groups():
    # 2 qualified thirds from groups A and C; two slots allowing {A,B} and {C,D}
    qualified = [dict(team="TA", group="A", pts=5, gd=1, gf=2),
                 dict(team="TC", group="C", pts=4, gd=0, gf=1)]
    slots = [frozenset("AB"), frozenset("CD")]
    assigned = bk.assign_thirds(qualified, slots)
    assert assigned[0]["group"] == "A"   # slot 0 ({A,B}) -> the group-A team
    assert assigned[1]["group"] == "C"   # slot 1 ({C,D}) -> the group-C team
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_bracket.py -q`
Expected: FAIL (`AttributeError: qualify_thirds`).

- [ ] **Step 3: Implement (append to `scorito/model/bracket.py`)**

```python
import warnings

import numpy as np
from scipy.optimize import linear_sum_assignment

_BIG = 1e6


def qualify_thirds(thirds):
    """The best 8 of the 12 third-placed teams by (pts, gd, gf). ``thirds`` is a list of
    dicts with keys team, group, pts, gd, gf."""
    return sorted(thirds, key=lambda d: (d["pts"], d["gd"], d["gf"]), reverse=True)[:8]


def assign_thirds(qualified, slot_allowed):
    """Assign the qualified thirds to the third-place slots respecting each slot's allowed
    groups. ``slot_allowed`` is a list of allowed-group sets (same length as qualified).
    Returns ``{slot_index: third_dict}``. Uses min-cost bipartite matching; warns and
    falls back if no constraint-respecting assignment exists (never expected for FIFA sets)."""
    n = len(qualified)
    cost = np.full((n, n), _BIG)
    for i, q in enumerate(qualified):
        for j, allowed in enumerate(slot_allowed):
            if q["group"] in allowed:
                cost[i, j] = 0.0
    rows, cols = linear_sum_assignment(cost)
    assigned = {}
    for i, j in zip(rows, cols):
        assigned[int(j)] = qualified[i]
        if cost[i, j] >= _BIG:
            warnings.warn("third-place slot assignment violated a group constraint")
    return assigned
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_bracket.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/bracket.py tests/test_bracket.py
git commit -m "feat(bracket): third-place qualification + constraint matching"
```

## Task 5: `tournament.advance_matrix`

**Files:**
- Create: `scorito/model/tournament.py`
- Test: `tests/test_tournament.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tournament.py
import pytest
from scorito.model import tournament as tn


def test_advance_matrix_complementary_and_monotonic():
    elo = {"Strong": 2100.0, "Mid": 1800.0, "Weak": 1500.0}
    P = tn.advance_matrix(["Strong", "Mid", "Weak"], elo)
    # complementary
    assert P[("Strong", "Weak")] + P[("Weak", "Strong")] == pytest.approx(1.0)
    # stronger team advances more often; all in (0,1)
    assert P[("Strong", "Weak")] > P[("Mid", "Weak")] > 0.5
    assert 0.0 < P[("Weak", "Strong")] < 0.5
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_tournament.py -q`
Expected: FAIL (`ModuleNotFoundError: scorito.model.tournament`).

- [ ] **Step 3: Implement**

```python
# scorito/model/tournament.py
"""Full-tournament Monte-Carlo -> P(win) + advancement for all 48 teams.

Group matches are sampled from their (odds/Elo) grids; knockout ties use a precomputed
Elo advance matrix (no KO odds exist). Reuses the group-sim primitives."""
import numpy as np

from scorito import config
from scorito.model.bracket import (GroupPos, LoserOf, ThirdSlot, WinnerOf,
                                    assign_thirds, qualify_thirds)
from scorito.model.goals import goals_from_elo
from scorito.model.grid import build_grid
from scorito.model.group_sim import _award, _rank_table, _sample_scores

ROUND_NEXT = {
    "Round of 32": "r16",
    "Round of 16": "qf",
    "Quarter-final": "sf",
    "Semi-final": "final",
    "Final": "win",
}


def advance_matrix(teams, elo):
    """``{(A, B): P(A wins a KO tie vs B)}`` = p_win + 0.5*p_draw from a neutral Elo grid."""
    P = {}
    for i, a in enumerate(teams):
        for b in teams[i + 1:]:
            l1, l2 = goals_from_elo(elo.get(a, 1500.0), elo.get(b, 1500.0))
            g = build_grid(l1, l2)
            pa = g.p_home + 0.5 * g.p_draw
            P[(a, b)] = pa
            P[(b, a)] = 1.0 - pa
    return P
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_tournament.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/tournament.py tests/test_tournament.py
git commit -m "feat(tournament): Elo knockout advance-probability matrix"
```

## Task 6: `tournament.simulate`

**Files:**
- Modify: `scorito/model/tournament.py`
- Test: `tests/test_tournament.py`

- [ ] **Step 1: Add the failing test**

```python
# append to tests/test_tournament.py
from scorito.model.bracket import KOMatch, GroupPos
from scorito.model.grid import build_grid


def _toy():
    # two groups of 3; in each, the "fav" is given dominant scoring grids
    gteams = {"A": ["AA", "AB", "AC"], "B": ["BA", "BB", "BC"]}
    matches = [("AA", "AB"), ("AA", "AC"), ("AB", "AC"),
               ("BA", "BB"), ("BA", "BC"), ("BB", "BC")]
    strong = build_grid(2.6, 0.2)   # home wins big
    even = build_grid(1.0, 1.0)
    grids = {("AA", "AB"): strong, ("AA", "AC"): strong, ("AB", "AC"): even,
             ("BA", "BB"): strong, ("BA", "BC"): strong, ("BB", "BC"): even}
    # AA and BA win their groups; AA hugely stronger by Elo -> wins the final
    elo = {"AA": 2400, "AB": 1500, "AC": 1500, "BA": 1700, "BB": 1500, "BC": 1500}
    bracket = [KOMatch(num=1, round="Final", team1=GroupPos(1, "A"), team2=GroupPos(1, "B"))]
    return gteams, matches, grids, elo, bracket


def test_simulate_probs_sum_to_one_and_favor_strongest():
    gteams, matches, grids, elo, bracket = _toy()
    out = tn.simulate(gteams, matches, grids, elo, bracket, sims=2000, seed=1)
    assert sum(out["win"].values()) == pytest.approx(1.0, abs=1e-9)
    assert out["win"]["AA"] > 0.6                 # dominant team usually champion
    assert out["win"]["AA"] == max(out["win"].values())


def test_simulate_is_seed_deterministic():
    gteams, matches, grids, elo, bracket = _toy()
    a = tn.simulate(gteams, matches, grids, elo, bracket, sims=500, seed=7)
    b = tn.simulate(gteams, matches, grids, elo, bracket, sims=500, seed=7)
    assert a["win"] == b["win"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_tournament.py -q`
Expected: FAIL (`AttributeError: simulate`).

- [ ] **Step 3: Implement (append to `scorito/model/tournament.py`)**

```python
def _resolve(ref, place, slot_team, winners, losers, num, side):
    if isinstance(ref, GroupPos):
        return place[ref.group][ref.pos - 1]
    if isinstance(ref, ThirdSlot):
        return slot_team[(num, side)]
    if isinstance(ref, WinnerOf):
        return winners[ref.num]
    if isinstance(ref, LoserOf):
        return losers[ref.num]
    raise ValueError(f"Unresolvable ref {ref!r}")


def simulate(gteams, group_matches, group_grids, elo, bracket, sims=config.MC_SIMS, seed=0):
    """Monte-Carlo the whole tournament. Returns
    ``{"win": {team: P}, "advance": {team: {"r16","qf","sf","final","win": P}}}``."""
    rng = np.random.default_rng(seed)
    all_teams = sorted({t for ts in gteams.values() for t in ts})
    P = advance_matrix(all_teams, elo)
    sampled = _sample_scores(group_matches, group_grids, sims, rng)

    grp_matches = {g: [] for g in gteams}
    for (a, b) in group_matches:
        for g, ts in gteams.items():
            if a in ts and b in ts:
                grp_matches[g].append((a, b))
                break

    # third-place slots, in a fixed order, with their (match num, side) and allowed groups
    slot_locs = []
    for m in bracket:
        for side, ref in (("t1", m.team1), ("t2", m.team2)):
            if isinstance(ref, ThirdSlot):
                slot_locs.append((m.num, side, ref.allowed))

    adv = {t: dict(r16=0, qf=0, sf=0, final=0, win=0) for t in all_teams}
    for s in range(sims):
        place, thirds = {}, []
        for g, ts in gteams.items():
            stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
            h2h = {}
            for (a, b) in grp_matches[g]:
                ga, gb = int(sampled[(a, b)][0][s]), int(sampled[(a, b)][1][s])
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
        for m in bracket:
            t1 = _resolve(m.team1, place, slot_team, winners, losers, m.num, "t1")
            t2 = _resolve(m.team2, place, slot_team, winners, losers, m.num, "t2")
            if rng.random() < P[(t1, t2)]:
                w, l = t1, t2
            else:
                w, l = t2, t1
            winners[m.num], losers[m.num] = w, l
            key = ROUND_NEXT.get(m.round)
            if key:
                adv[w][key] += 1

    advance = {t: {k: adv[t][k] / sims for k in adv[t]} for t in all_teams}
    return {"win": {t: advance[t]["win"] for t in all_teams}, "advance": advance}
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_tournament.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/model/tournament.py tests/test_tournament.py
git commit -m "feat(tournament): full-tournament Monte-Carlo simulate()"
```

## Task 7: wire into `main` + `report` (advancement)

**Files:**
- Modify: `scorito/report.py` (RunResult + champion table)
- Modify: `scorito/main.py` (run orchestration)
- Test: `tests/test_main_smoke.py`, `tests/test_report.py`

- [ ] **Step 1: Add `advance` to RunResult + advancement columns** in `scorito/report.py`

Add a field to the `RunResult` dataclass (after `meta`):
```python
    advance: dict = field(default_factory=dict)   # team -> {"r16","qf","sf","final","win"}
```
Replace the champion table block (the `"| Team | P(win) | EV | Est. pool share | Leverage |"` header, its separator, and the `for r in result.champion[:5]` loop) with:
```python
    L.append("| Team | P(win) | EV | Share | Lev | R16 | QF | SF | Final |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in result.champion[:5]:
        a = result.advance.get(r.team, {})
        L.append(f"| {r.team} | {r.p_win:.1%} | {r.ev_points:.0f} | {r.est_share:.0%} | "
                 f"{r.leverage:.4f} | {a.get('r16', 0):.0%} | {a.get('qf', 0):.0%} | "
                 f"{a.get('sf', 0):.0%} | {a.get('final', 0):.0%} |")
```

- [ ] **Step 2: Wire the simulation into `scorito/main.py`**

Add imports near the top (with the other model imports):
```python
from scorito.model import bracket as bracket_mod
from scorito.model import tournament
from scorito.data.priors import blended_probs, blend_champion_probs
from scorito.model.champion import recommend_champion
```
(remove any now-duplicate `recommend_champion` import.) In `run`, accumulate all group grids: initialise `all_grids = {}` before the group loop, and inside the loop after `grids[(m.team1, m.team2)] = build_grid(l1, l2)` add `all_grids.update(grids)` (or build into `all_grids` directly). After the group loop and `team_factors`, replace the existing champion line with:
```python
    brk = bracket_mod.load_bracket(fixtures_src or _default_fixtures())
    group_match_keys = [(m.team1, m.team2) for m in matches]
    sim = tournament.simulate(gteams, group_match_keys, all_grids, elo_map, brk,
                              sims=sims, seed=seed)
    pwin = blend_champion_probs(sim["win"], blended_probs())
    champion = recommend_champion(pwin, pool_size, risk)
```
Pass `advance=sim["advance"]` into the `RunResult(...)` constructor.

- [ ] **Step 3: Update the smoke test** `tests/test_main_smoke.py`

Ensure it still asserts a run completes; add a champion/advancement assertion:
```python
    assert len(res.champion) == 48
    assert res.advance and abs(sum(res.champion[i].p_win for i in range(len(res.champion))) - 1.0) < 0.05
```
(Place these alongside the existing assertions in the smoke test's run.)

- [ ] **Step 4: Update `tests/test_report.py`** champion fixture to include `advance`

In the `build_csv_rows`/render test, construct `RunResult(...)` (or the champion list) so a render with `advance={"France": {...}}` doesn't KeyError. If the test calls `_render_markdown`, pass `advance={r.team: {"r16":0.5,"qf":0.3,"sf":0.2,"final":0.1,"win":0.05} for r in champion}`. (`build_csv_rows` is unchanged — champion rows still use p_win/share/ev.)

- [ ] **Step 5: Run the suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS (all, incl. new bracket/tournament/priors).

- [ ] **Step 6: Commit**

```bash
git add scorito/report.py scorito/main.py tests/test_main_smoke.py tests/test_report.py
git commit -m "feat(champion): wire tournament MC into run + advancement in report"
```

## Task 8: real run + README

**Files:**
- Modify: `README.md`
- (verification)

- [ ] **Step 1: Real run with the cached odds feed**

Run: `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --pool-size 40 --risk balanced`
Expected: completes; `out/report.md` champion table shows all-48-derived probabilities + R16/QF/SF/Final %; sanity-check the favourites (Spain/France/England high) and that France's path reflects its hard group.

- [ ] **Step 2: Note the champion model in README** — under the existing model description, add one line that champion `P(win)` is a full-tournament Monte-Carlo (all 48, draw-aware) blended with market via `CHAMPION_MARKET_WEIGHT`.

- [ ] **Step 3: Final suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: champion P(win) is now a full-tournament Monte-Carlo"
```

---

## Self-Review

- **Spec coverage:** §6 bracket → Tasks 3-4; §7 tournament (advance matrix + simulate) → Tasks 5-6; §8 blend → Task 1; §9 integration (champion sig, main wiring, report advancement) → Tasks 2,7; config weight → Task 1; testing §11 → every task TDD; perf §12 → Task 8 real run. All covered.
- **Placeholder scan:** none — every code step is complete and runnable.
- **Type consistency:** `simulate` returns `{"win":..., "advance":...}` consumed by `main` (pwin from `sim["win"]`, `advance=sim["advance"]`) and `report` (`result.advance.get(team)`); `recommend_champion(pwin, pool_size, risk)` matches its call in `main` and `test_champion`; `blend_champion_probs(mc, market, weight)` matches Task 1 + the `main` call (weight defaulted from config); bracket ref types (`GroupPos/ThirdSlot/WinnerOf/LoserOf`) defined in Task 3 and consumed by `_resolve`/`simulate` in Task 6; `assign_thirds(qualified, slot_allowed)` signature matches its call in `simulate`.
- **Open risk:** `simulate` over `MC_SIMS=20000` does a Python per-sim loop (~12 group tables + 32 KO resolves + an 8×8 assignment each) — expected a few-to-~30s; if too slow, lower sims via the `sims` arg (Task 8 will reveal actual timing).
