# Opponent-specific topscorer hand-fallback — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** In `build_expected_goals`, score unpriced (hand-fallback) topscorer matches with the opponent-specific team expected-goals instead of the group-average team_factor, removing the easy-opener inflation (Wirtz).

**Architecture:** Add `match_lams`/`avg_lam` to `build_expected_goals`; `main` passes the per-match λ it already computes. Backward-compatible (no args → today's group-average).

**Tech Stack:** Python 3.12, pytest.

---

## Task 1: opponent-specific hand fallback (`topscorers.py`)

**Files:** Modify `scorito/model/topscorers.py`, `tests/test_topscorers.py`

- [ ] **Step 1: Failing test** — append to `tests/test_topscorers.py`:
```python
def test_build_expected_goals_opponent_specific_hand_fallback():
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals
    matches = [SimpleNamespace(team1="DE", team2="Minnow"), SimpleNamespace(team1="DE", team2="Tough")]
    cand = dict(name="X", team="DE", position="MID", g90=0.2, start_prob=1.0)
    tf = {"DE": 2.0}                                   # inflated group-average factor
    lams = {("DE", "Minnow"): (3.0, 0.3), ("DE", "Tough"): (1.0, 1.2)}   # DE scores 3 vs Minnow, 1 vs Tough
    out = build_expected_goals([cand], matches, {}, tf, match_lams=lams, avg_lam=1.5)[0]
    expected = 0.2 * 1.0 * (3.0 / 1.5) + 0.2 * 1.0 * (1.0 / 1.5)   # opponent-specific per match
    assert abs(out["exp_goals"] - expected) < 1e-9
    # backward-compat: no match_lams -> group-average team_factor (2.0) for every match
    out2 = build_expected_goals([cand], matches, {}, tf)[0]
    assert abs(out2["exp_goals"] - 2 * (0.2 * 1.0 * 2.0)) < 1e-9
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_topscorers.py::test_build_expected_goals_opponent_specific_hand_fallback -q` → FAIL (`build_expected_goals` has no `match_lams`).
- [ ] **Step 3: Implement** — in `scorito/model/topscorers.py` change the `build_expected_goals` signature line to:
```python
def build_expected_goals(candidates, matches, atgs_map, team_factors,
                         match_lams=None, avg_lam=None, margin=config.ATGS_MARGIN):
```
and replace the `else:` hand-fallback block
```python
            else:
                total += c["g90"] * c["start_prob"] * team_factors.get(c["team"], 1.0) \
                    + PEN_BONUS * pen_share / n
```
with:
```python
            else:
                lam = match_lams.get((h, a)) if match_lams else None
                if lam and avg_lam:                       # opponent-specific team scoring this match
                    team_lam = lam[0] if c["team"] == h else lam[1]
                    factor = team_lam / avg_lam
                else:                                     # backward-compatible: group-average
                    factor = team_factors.get(c["team"], 1.0)
                total += c["g90"] * c["start_prob"] * factor + PEN_BONUS * pen_share / n
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_topscorers.py -q` → PASS (new + existing).
- [ ] **Step 5: Commit** `git add scorito/model/topscorers.py tests/test_topscorers.py && git commit -m "feat(topscorers): opponent-specific hand fallback in build_expected_goals (fix easy-opener tilt)"`

## Task 2: wire per-match λ from `main.py`

**Files:** Modify `scorito/main.py`

- [ ] **Step 1: Init the map** — change `    all_grids = {}` to:
```python
    all_grids = {}
    match_lams = {}
```
- [ ] **Step 2: Capture per-match λ** — after `            team_lambda[m.team2].append(l2)` add:
```python
            match_lams[(m.team1, m.team2)] = (l1, l2)
```
- [ ] **Step 3: Pass into the call** — change `        kept = build_expected_goals(kept, matches, atgs_map, team_factors)` to:
```python
        kept = build_expected_goals(kept, matches, atgs_map, team_factors,
                                    match_lams=match_lams, avg_lam=avg)
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/main.py && git commit -m "feat(topscorers): feed per-match team lambda into build_expected_goals"`

## Task 3: validate, document, finish

**Files:** Create `docs/opponent-specific-fallback-2026-06-09.md`; verification + merge

- [ ] **Step 1: Real run + before/after** — run the topscorer breakdown with the cached feeds:
```bash
.venv/bin/python - <<'PY'
import json
from collections import defaultdict
from scorito.data import fixtures, odds, elo
from scorito.data.fixtures import group_teams
from scorito.data.topscorer_candidates import CANDIDATES
from scorito import config
from scorito.model.goals import expected_goals
from scorito.model.topscorers import build_expected_goals, score_candidate
from scorito.main import _default_fixtures
src = _default_fixtures(); matches = fixtures.load_fixtures(src); gteams = group_teams(matches)
ats = sorted({t for ts in gteams.values() for t in ts}); em = elo.get_elo(ats)
eg = dict(em)
for h in config.HOSTS:
    if h in eg: eg[h] += config.HOST_ELO_BONUS
omap = odds.parse_odds(json.load(open("data/cache/odds_raw.json")))
amap = odds.parse_atgs(json.load(open("data/cache/atgs_raw.json")))
tl = defaultdict(list); ml = {}
for m in matches:
    l1, l2 = expected_goals(m, omap, eg); tl[m.team1].append(l1); tl[m.team2].append(l2); ml[(m.team1, m.team2)] = (l1, l2)
means = {t: sum(v)/len(v) for t, v in tl.items()}; avg = sum(means.values())/len(means); tf = {t: means[t]/avg for t in means}
def ranked(use):
    kept = build_expected_goals(CANDIDATES, matches, amap, tf, match_lams=(ml if use else None), avg_lam=(avg if use else None))
    return sorted(((c["name"], round(score_candidate(c, tf), 1)) for c in kept), key=lambda x: -x[1])[:8]
print("BEFORE (group-avg tf):", ranked(False))
print("AFTER  (opponent-spec):", ranked(True))
PY
```
  Expected: AFTER, Wirtz's EV drops (~25.9→~20) and **Kane leads**; other easy-opener players (Yamal) deflate; tough-opener players unaffected. Then `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --atgs-file data/cache/atgs_raw.json --winner-file data/cache/winner_raw.json --risk balanced` and confirm the report's topscorer six are sensible.
- [ ] **Step 2: Finding doc** — create `docs/opponent-specific-fallback-2026-06-09.md`: the before/after topscorer ranking, the Wirtz numbers, and the principle (unpriced games now use opponent-specific expected goals, removing the easy-opener inflation).
- [ ] **Step 3: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 4: Commit** `git add docs/opponent-specific-fallback-2026-06-09.md && git commit -m "docs: opponent-specific hand-fallback finding (de-inflates easy-opener topscorers)"`

---

## Self-Review
- **Spec coverage:** fix §3 → Task 1; wiring §4 → Task 2; validation §5 → Task 3; backward-compat §6 → Task 1 (test asserts identical without args); testing §7 → Task 1. Covered.
- **Placeholder scan:** none — complete code + runnable diagnostic.
- **Type consistency:** `build_expected_goals(..., match_lams, avg_lam, margin)` matches the `main` call (Task 2) and the test (Task 1); `match_lams` keyed `(m.team1, m.team2)` matches the `(h, a)` lookup (both from the same `matches`); `avg_lam` is `main`'s existing `avg`.
- **Backward-compat:** `match_lams=None` → group-average `team_factor`, byte-identical to today (Task 1 test asserts it); only the ATGS-blend path (where `build_expected_goals` runs) is affected.
