# Validation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scorito/eval/` to (1) grade our live WC2026 picks vs. baselines as results arrive and (2) calibrate the score/outcome model on past tournaments — making model changes provable.

**Architecture:** A pure `metrics.py` core (log-loss, Brier, reliability, realized-Scorito-points). Phase 1 (live scorecard) reuses existing loaders + the openfootball score field. Phase 2 (historical calibration) computes Elo ourselves from the free international-results CSV (no fragile historical-odds/Elo scraping), replays past tournaments through the Elo→grid path, and sweeps `DC_RHO / NEUTRAL_AVG_TOTAL / ELO_GOAL_DIVISOR` under leave-one-tournament-out CV.

**Tech Stack:** Python 3.12, numpy, penaltyblog (existing), pytest. No new deps.

> **Spec refinement (flag for review):** the spec said historical Elo from eloratings.net; that site only serves *current* ratings and historical date-stamped retrieval isn't cleanly free. This plan instead **computes Elo from the free `martj42/international_results` CSV** (results 1872→present). More reproducible, and a reusable rating source. Live results still come from the existing openfootball feed.

---

## File Structure

```
scorito/eval/
  __init__.py     # empty package marker
  metrics.py      # PURE: log_loss, brier, reliability_bins, match_points, standings_points, topscorer_points
  results.py      # parse actual scores from openfootball JSON; build actual group tables
  picks.py        # parse out/picks.csv into structured picks (scorelines, standing, champion, topscorers)
  scorecard.py    # realized points for our picks + baselines, per component, incremental
  elohist.py      # compute Elo through international-match history -> pre-match ratings
  datasets.py     # load past-tournament matches (martj42 CSV) joined with pre-match Elo
  calibrate.py    # replay Elo->grid, metrics, constant sweep + leave-one-tournament-out CV
  __main__.py     # CLI: `python -m scorito.eval scorecard|calibrate`
tests/
  test_eval_metrics.py
  test_eval_scorecard.py
  test_eval_elohist.py
  test_eval_calibrate.py
  fixtures/eval/  # tiny JSON/CSV fixtures
```

Reused as-is: `scorito.config`, `scorito.model.goals.goals_from_elo`, `scorito.model.grid.build_grid`, `scorito.model.group_sim._rank_table`/`_award`, `scorito.data.fixtures`.

---

# PHASE 1 — Live scorecard (metrics + scorecard + CLI)

## Task 1: metrics.py — probabilistic metrics

**Files:**
- Create: `scorito/eval/__init__.py` (empty)
- Create: `scorito/eval/metrics.py`
- Test: `tests/test_eval_metrics.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_eval_metrics.py
import math
import pytest
from scorito.eval import metrics


def test_log_loss_perfect_and_clamped():
    assert metrics.log_loss([1.0, 0.0, 0.0], 0) == pytest.approx(0.0, abs=1e-9)
    # clamped: never infinite even if prob is 0
    assert metrics.log_loss([0.0, 1.0, 0.0], 0) < 40 and metrics.log_loss([0.0, 1.0, 0.0], 0) > 30


def test_log_loss_known_value():
    assert metrics.log_loss([0.5, 0.3, 0.2], 1) == pytest.approx(-math.log(0.3), abs=1e-9)


def test_brier_known_value():
    # outcome idx 0: (0.7-1)^2 + (0.2-0)^2 + (0.1-0)^2 = 0.09+0.04+0.01 = 0.14
    assert metrics.brier([0.7, 0.2, 0.1], 0) == pytest.approx(0.14, abs=1e-9)


def test_reliability_bins_groups_by_predicted():
    pairs = [(0.05, False), (0.05, False), (0.95, True), (0.95, True)]
    bins = metrics.reliability_bins(pairs, nbins=10)
    assert bins[0] == (pytest.approx(0.05), pytest.approx(0.0), 2)
    assert bins[9] == (pytest.approx(0.95), pytest.approx(1.0), 2)
    assert bins[5] == (None, None, 0)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_metrics.py -q`
Expected: FAIL (`ModuleNotFoundError: scorito.eval`).

- [ ] **Step 3: Implement**

```python
# scorito/eval/__init__.py  (empty file)
```

```python
# scorito/eval/metrics.py
"""Pure evaluation metrics: probabilistic accuracy + realized Scorito points."""
import math

from scorito import config

_EPS = 1e-15


def log_loss(probs, outcome_idx: int) -> float:
    """Negative log of the probability assigned to the realised outcome (clamped)."""
    p = min(1.0, max(_EPS, probs[outcome_idx]))
    return -math.log(p)


def brier(probs, outcome_idx: int) -> float:
    """Sum of squared error vs the one-hot outcome."""
    return sum((p - (1.0 if i == outcome_idx else 0.0)) ** 2 for i, p in enumerate(probs))


def reliability_bins(pairs, nbins: int = 10):
    """``pairs`` = [(predicted_prob, outcome_bool)]. Returns one (mean_pred, mean_obs,
    count) tuple per equal-width bin; empty bins are (None, None, 0)."""
    buckets = [[] for _ in range(nbins)]
    for p, o in pairs:
        idx = min(nbins - 1, max(0, int(p * nbins)))
        buckets[idx].append((p, 1.0 if o else 0.0))
    out = []
    for b in buckets:
        if b:
            out.append((sum(x[0] for x in b) / len(b),
                        sum(x[1] for x in b) / len(b), len(b)))
        else:
            out.append((None, None, 0))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_metrics.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/__init__.py scorito/eval/metrics.py tests/test_eval_metrics.py
git commit -m "feat(eval): probabilistic metrics (log-loss, Brier, reliability)"
```

## Task 2: metrics.py — realized Scorito points

**Files:**
- Modify: `scorito/eval/metrics.py`
- Test: `tests/test_eval_metrics.py`

- [ ] **Step 1: Add failing tests**

```python
# append to tests/test_eval_metrics.py
def test_match_points_exact_toto_miss():
    assert metrics.match_points((1, 0), (1, 0)) == 45   # exact
    assert metrics.match_points((2, 1), (1, 0)) == 30   # right home win, wrong score
    assert metrics.match_points((1, 1), (1, 0)) == 0    # wrong outcome
    assert metrics.match_points((0, 0), (2, 2)) == 30   # both draws, wrong score


def test_standings_points_counts_correct_positions():
    assert metrics.standings_points(["A", "B", "C", "D"], ["A", "C", "B", "D"]) == 50  # A,D right


def test_topscorer_points_uses_position_multiplier():
    picks = [dict(name="Kane", position="ATT"), dict(name="Hakimi", position="DEF")]
    goals = {"Kane": 3, "Hakimi": 1}
    assert metrics.topscorer_points(picks, goals) == 3 * 8 + 1 * 32
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_metrics.py -q`
Expected: FAIL (`AttributeError: match_points`).

- [ ] **Step 3: Implement (append to metrics.py)**

```python
def _sign(h, a) -> int:
    return (h > a) - (h < a)


def match_points(pick, actual) -> int:
    """45 exact, else 30 if the 1/X/2 outcome matches, else 0."""
    if tuple(pick) == tuple(actual):
        return config.PTS_EXACT
    if _sign(*pick) == _sign(*actual):
        return config.PTS_TOTO
    return 0


def standings_points(predicted_table, actual_table) -> int:
    """25 per team whose predicted finishing position matches the actual one."""
    return config.PTS_POSITION * sum(
        1 for p, a in zip(predicted_table, actual_table) if p == a
    )


def topscorer_points(picks, scorer_goals) -> int:
    """Σ goals × position multiplier (ATT 8 / MID 16 / DEF,GK 32) over our picks."""
    return sum(int(scorer_goals.get(c["name"], 0)) * config.TOPSCORER_MULT[c["position"]]
               for c in picks)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_metrics.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/metrics.py tests/test_eval_metrics.py
git commit -m "feat(eval): realized Scorito points (match/standings/topscorer)"
```

## Task 3: results.py — actual scores + actual group tables

**Files:**
- Create: `scorito/eval/results.py`
- Test: `tests/test_eval_scorecard.py`
- Fixture: `tests/fixtures/eval/wc_played.json`

- [ ] **Step 1: Write fixture + failing test**

```json
// tests/fixtures/eval/wc_played.json
{"name": "T", "matches": [
  {"round": "Matchday 1", "date": "2026-06-11", "team1": "Mexico", "team2": "South Africa",
   "group": "Group A", "score": {"ft": [2, 0]}},
  {"round": "Matchday 1", "date": "2026-06-11", "team1": "South Korea", "team2": "Czech Republic",
   "group": "Group A", "score": {"ft": [1, 1]}}
]}
```

```python
# tests/test_eval_scorecard.py
from scorito.eval import results


def test_played_results_parses_ft_scores():
    r = results.played_results("tests/fixtures/eval/wc_played.json")
    assert r[("Mexico", "South Africa")] == (2, 0)
    assert r[("South Korea", "Czech Republic")] == (1, 1)


def test_unplayed_matches_are_skipped(tmp_path):
    p = tmp_path / "f.json"
    p.write_text('{"matches":[{"team1":"A","team2":"B","group":"Group A"}]}')
    assert results.played_results(str(p)) == {}
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py -q`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

```python
# scorito/eval/results.py
"""Actual results from an openfootball-format JSON (scores fill in as matches play)."""
import json

from scorito.model.group_sim import _award, _rank_table


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def played_results(path):
    """``{(team1, team2): (home_goals, away_goals)}`` for matches that have a final score."""
    out = {}
    for m in _load(path).get("matches", []):
        ft = (m.get("score") or {}).get("ft")
        if ft and len(ft) == 2:
            out[(m["team1"], m["team2"])] = (int(ft[0]), int(ft[1]))
    return out


def actual_group_tables(path):
    """``{group: [team,...]}`` final tables, only for groups whose 6 matches all have scores."""
    groups = {}
    for m in _load(path).get("matches", []):
        grp = (m.get("group") or "").replace("Group ", "").strip()
        if not grp:
            continue
        groups.setdefault(grp, []).append(m)
    tables = {}
    for grp, ms in groups.items():
        played = [(m, (m.get("score") or {}).get("ft")) for m in ms]
        if len(ms) != 6 or any(ft is None for _, ft in played):
            continue  # group incomplete
        teams = []
        for m in ms:
            for t in (m["team1"], m["team2"]):
                if t not in teams:
                    teams.append(t)
        stats = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
        res = {}
        for m, ft in played:
            res[(m["team1"], m["team2"])] = (int(ft[0]), int(ft[1]))
            _award(stats[m["team1"]], stats[m["team2"]], int(ft[0]), int(ft[1]))
        tables[grp] = _rank_table(stats, h2h=res, rng=None)
    return tables
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/results.py tests/test_eval_scorecard.py tests/fixtures/eval/wc_played.json
git commit -m "feat(eval): parse actual scores and final group tables from openfootball JSON"
```

## Task 4: picks.py — parse our committed picks

**Files:**
- Create: `scorito/eval/picks.py`
- Test: `tests/test_eval_scorecard.py`
- Fixture: `tests/fixtures/eval/picks.csv`

> NOTE on schema: `report.build_csv_rows` writes rows `type,group,item,detail,value`:
> - match → `item="A vs B"`, `detail="h-a"`; standing → `item="1. Team"`;
> - champion → `item=Team`; topscorer → `item="Name (Team, POS)"`.

- [ ] **Step 1: Write fixture + failing test**

```
// tests/fixtures/eval/picks.csv
type,group,item,detail,value
match,A,Mexico vs South Africa,1-0,28.2
standing,A,1. Mexico,,
standing,A,2. South Korea,,
standing,A,3. Czech Republic,,
standing,A,4. South Africa,,
champion,,Spain,p_win=0.16,40.0
topscorer,,Harry Kane (England, ATT),PEN,30.7
```

```python
# append to tests/test_eval_scorecard.py
from scorito.eval import picks as picks_mod


def test_parse_picks_csv():
    p = picks_mod.load_picks("tests/fixtures/eval/picks.csv")
    assert p["scorelines"][("Mexico", "South Africa")] == (1, 0)
    assert p["standings"]["A"] == ["Mexico", "South Korea", "Czech Republic", "South Africa"]
    assert p["champion"] == "Spain"
    assert p["topscorers"] == [dict(name="Harry Kane", team="England", position="ATT")]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py::test_parse_picks_csv -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# scorito/eval/picks.py
"""Parse out/picks.csv (schema from scorito.report.build_csv_rows) into structured picks."""
import csv
import re

_TS = re.compile(r"^(?P<name>.+?)\s*\((?P<team>.+),\s*(?P<pos>GK|DEF|MID|ATT)\)\s*$")


def load_picks(path):
    scorelines, standings, champion, topscorers = {}, {}, None, []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = row["type"]
            if t == "match":
                a, b = row["item"].split(" vs ")
                h, w = row["detail"].split("-")
                scorelines[(a.strip(), b.strip())] = (int(h), int(w))
            elif t == "standing":
                team = row["item"].split(". ", 1)[1]
                standings.setdefault(row["group"], []).append(team)
            elif t == "champion":
                champion = row["item"].strip()
            elif t == "topscorer":
                m = _TS.match(row["item"])
                if m:
                    topscorers.append(dict(name=m["name"].strip(),
                                           team=m["team"].strip(), position=m["pos"]))
    return dict(scorelines=scorelines, standings=standings,
                champion=champion, topscorers=topscorers)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py::test_parse_picks_csv -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/picks.py tests/test_eval_scorecard.py tests/fixtures/eval/picks.csv
git commit -m "feat(eval): parse picks.csv into structured picks"
```

## Task 5: scorecard.py — realized points vs baselines

**Files:**
- Create: `scorito/eval/scorecard.py`
- Test: `tests/test_eval_scorecard.py`

- [ ] **Step 1: Write failing test**

```python
# append to tests/test_eval_scorecard.py
from scorito.eval import scorecard


def test_scorecard_scores_played_matches_and_baseline():
    our = {"scorelines": {("Mexico", "South Africa"): (1, 0),
                          ("South Korea", "Czech Republic"): (2, 0)},
           "standings": {}, "champion": None, "topscorers": []}
    actual = {("Mexico", "South Africa"): (2, 0),          # our 1-0 -> toto 30
              ("South Korea", "Czech Republic"): (1, 1)}    # our 2-0 -> miss 0
    sc = scorecard.score_scorelines(our["scorelines"], actual)
    assert sc["ours"] == 30
    # always-1-0 baseline: MEX 1-0 vs 2-0 -> 30 ; KOR 1-0 vs 1-1 -> 0
    assert sc["baseline_1_0"] == 30
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py::test_scorecard_scores_played_matches_and_baseline -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# scorito/eval/scorecard.py
"""Realized Scorito points for our picks vs. baselines, scored incrementally."""
import json
import os

from scorito.eval import metrics

# Market top-6 by June-2026 Golden-Boot odds (see docs/topscorer-research-2026-06-08.md),
# all in confirmed squads. Baseline only.
MARKET_TOP6 = [
    dict(name="Kylian Mbappe", team="France", position="ATT"),
    dict(name="Harry Kane", team="England", position="ATT"),
    dict(name="Erling Haaland", team="Norway", position="ATT"),
    dict(name="Mikel Oyarzabal", team="Spain", position="ATT"),
    dict(name="Lionel Messi", team="Argentina", position="ATT"),
    dict(name="Cristiano Ronaldo", team="Portugal", position="ATT"),
]


def score_scorelines(our_scorelines, actual):
    """Our scoreline points vs the always-1-0 baseline, over played matches."""
    ours = base = 0
    for key, act in actual.items():
        if key in our_scorelines:
            ours += metrics.match_points(our_scorelines[key], act)
        base += metrics.match_points((1, 0), act)
    return {"ours": ours, "baseline_1_0": base, "n_played": len(actual)}


def score_standings(our_standings, actual_tables):
    ours = sum(metrics.standings_points(our_standings[g], actual_tables[g])
               for g in actual_tables if g in our_standings)
    return {"ours": ours, "n_groups": len(actual_tables)}


def score_topscorers(our_topscorers, scorer_goals):
    return {"ours": metrics.topscorer_points(our_topscorers, scorer_goals),
            "baseline_market": metrics.topscorer_points(MARKET_TOP6, scorer_goals)}


def load_scorers(path="data/wc2026_scorers.json"):
    """Optional ``{player_name: group_stage_goals}``; absent -> topscorer grading off."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_scorecard.py -q`
Expected: PASS (all scorecard tests).

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/scorecard.py tests/test_eval_scorecard.py
git commit -m "feat(eval): scorecard scoring vs baselines (scorelines/standings/topscorers)"
```

## Task 6: __main__.py — `scorecard` CLI

**Files:**
- Create: `scorito/eval/__main__.py`
- Test: manual smoke (documented)

- [ ] **Step 1: Implement the CLI (scorecard subcommand)**

```python
# scorito/eval/__main__.py
"""CLI: python -m scorito.eval scorecard|calibrate"""
import argparse

from scorito.eval import picks as picks_mod
from scorito.eval import results as results_mod
from scorito.eval import scorecard as sc


def _scorecard(args):
    our = picks_mod.load_picks(args.picks)
    actual = results_mod.played_results(args.results)
    tables = results_mod.actual_group_tables(args.results)
    line = sc.score_scorelines(our["scorelines"], actual)
    stand = sc.score_standings(our["standings"], tables)
    print(f"Scorelines ({line['n_played']} played): ours {line['ours']} "
          f"vs always-1-0 {line['baseline_1_0']}")
    print(f"Standings ({stand['n_groups']} groups done): ours {stand['ours']}")
    goals = sc.load_scorers(args.scorers)
    if goals is None:
        print(f"Topscorers: (no {args.scorers} -> grading off)")
    else:
        ts = sc.score_topscorers(our["topscorers"], goals)
        print(f"Topscorers: ours {ts['ours']} vs market-top6 {ts['baseline_market']}")
    total = line["ours"] + stand["ours"]
    print(f"TOTAL (ex-champion): ours {total} vs always-1-0+chalk {line['baseline_1_0'] + stand['ours']}")


def main():
    p = argparse.ArgumentParser(prog="scorito.eval")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scorecard")
    s.add_argument("--picks", default="out/picks.csv")
    s.add_argument("--results", default="data/cache/worldcup2026.json")
    s.add_argument("--scorers", default="data/wc2026_scorers.json")
    s.set_defaults(func=_scorecard)
    # calibrate subcommand wired in Task 10
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test**

Run: `.venv/bin/python -m scorito.eval scorecard --picks tests/fixtures/eval/picks.csv --results tests/fixtures/eval/wc_played.json`
Expected: prints scoreline/standings/topscorer lines without error (topscorers off unless the file exists).

- [ ] **Step 3: Commit**

```bash
git add scorito/eval/__main__.py
git commit -m "feat(eval): scorecard CLI"
```

---

# PHASE 2 — Historical calibration (self-Elo + datasets + calibrate)

## Task 7: elohist.py — compute Elo through match history

**Files:**
- Create: `scorito/eval/elohist.py`
- Test: `tests/test_eval_elohist.py`

> World-Football-Elo update: `R' = R + K·G·(W − We)`, `We = 1/(10^(−dr/400)+1)`,
> `dr = R_home + HA − R_away`, `G` = goal-difference multiplier (1; 1.5 if diff 2;
> `(11+diff)/8` if diff ≥ 3), `K=40` (tournament). `W` ∈ {1, 0.5, 0}. `HA=0` at neutral sites.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_eval_elohist.py
from scorito.eval import elohist


def test_expected_score_symmetry():
    assert elohist.expected(1500, 1500, ha=0) == 0.5


def test_higher_rated_gains_less_on_win():
    # equal teams, home wins 1-0 (G=1): winner gains K*1*(1-0.5)=20 at K=40
    ratings = {}
    pre = elohist.update(ratings, "A", "B", 1, 0, k=40, ha=0)
    assert pre == (1500.0, 1500.0)
    assert ratings["A"] == 1520.0 and ratings["B"] == 1480.0


def test_goal_diff_multiplier():
    assert elohist.goal_mult(1) == 1.0
    assert elohist.goal_mult(2) == 1.5
    assert elohist.goal_mult(3) == (11 + 3) / 8


def test_run_history_records_prematch_ratings():
    matches = [
        dict(date="2018-01-01", home="A", away="B", hg=1, ag=0, neutral=False),
        dict(date="2018-02-01", home="A", away="C", hg=0, ag=0, neutral=True),
    ]
    pre = elohist.run_history(matches)
    assert pre[0]["home_pre"] == 1500.0 and pre[0]["away_pre"] == 1500.0
    assert pre[1]["home_pre"] > 1500.0  # A won its first game
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_elohist.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# scorito/eval/elohist.py
"""Self-computed national-team Elo through match history (World-Football-Elo style).

Gives reproducible PRE-MATCH ratings for any historical fixture without scraping
date-stamped ratings. Used only by the calibration backtest."""
DEFAULT_K = 40.0
DEFAULT_HA = 65.0  # home advantage in Elo points (0 at neutral sites / tournaments)


def expected(r_home, r_away, ha=DEFAULT_HA):
    return 1.0 / (10 ** (-(r_home + ha - r_away) / 400.0) + 1.0)


def goal_mult(diff: int) -> float:
    diff = abs(diff)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11 + diff) / 8.0


def update(ratings, home, away, hg, ag, k=DEFAULT_K, ha=DEFAULT_HA):
    """Apply one result in place; return the (home_pre, away_pre) ratings."""
    rh = ratings.get(home, 1500.0)
    ra = ratings.get(away, 1500.0)
    we = expected(rh, ra, ha)
    w = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
    delta = k * goal_mult(hg - ag) * (w - we)
    ratings[home] = rh + delta
    ratings[away] = ra - delta
    return rh, ra


def run_history(matches, k=DEFAULT_K, ha=DEFAULT_HA):
    """``matches`` sorted ascending by date, each
    ``{date, home, away, hg, ag, neutral}``. Returns the same list annotated with
    ``home_pre``/``away_pre`` (ratings BEFORE that match)."""
    ratings, out = {}, []
    for m in sorted(matches, key=lambda x: x["date"]):
        h = 0.0 if m.get("neutral") else ha
        rh, ra = update(ratings, m["home"], m["away"], m["hg"], m["ag"], k=k, ha=h)
        out.append(dict(m, home_pre=rh, away_pre=ra))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_elohist.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/elohist.py tests/test_eval_elohist.py
git commit -m "feat(eval): self-computed historical Elo engine"
```

## Task 8: datasets.py — load past tournaments + pre-match Elo

**Files:**
- Create: `scorito/eval/datasets.py`
- Test: `tests/test_eval_calibrate.py`
- Fixture: `tests/fixtures/eval/intl_results.csv`

> DATA SOURCE: `https://raw.githubusercontent.com/martj42/international_results/master/results.csv`
> columns `date,home_team,away_team,home_score,away_score,tournament,city,country,neutral`.
> **First implementation step: fetch once, confirm the header matches, cache to
> `data/cache/history/intl_results.csv`.** `TOURNAMENTS` maps a label to the
> `tournament` value + year set used for evaluation.

- [ ] **Step 1: Write fixture + failing test**

```
// tests/fixtures/eval/intl_results.csv
date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
2017-06-01,A,B,2,1,Friendly,X,X,FALSE
2018-06-14,A,B,1,0,FIFA World Cup,Moscow,Russia,TRUE
2018-06-15,C,D,0,0,FIFA World Cup,Sochi,Russia,TRUE
```

```python
# tests/test_eval_calibrate.py
from scorito.eval import datasets


def test_load_intl_filters_tournament_and_builds_history():
    ds = datasets.load_tournament(
        "tests/fixtures/eval/intl_results.csv",
        tournament="FIFA World Cup", years={2018})
    # two WC matches in 2018; friendly excluded from the evaluation set
    assert len(ds["eval_matches"]) == 2
    # but the friendly IS used to warm up Elo (history precedes the tournament)
    m = ds["eval_matches"][0]
    assert {"home", "away", "hg", "ag", "home_pre", "away_pre", "neutral"} <= set(m)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_calibrate.py::test_load_intl_filters_tournament_and_builds_history -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# scorito/eval/datasets.py
"""Past-tournament datasets from the martj42 international-results CSV, annotated with
self-computed pre-match Elo (warmed up on all prior matches)."""
import csv

from scorito.eval import elohist

# label -> (tournament value in the CSV, set of years)
TOURNAMENTS = {
    "wc2014": ("FIFA World Cup", {2014}),
    "wc2018": ("FIFA World Cup", {2018}),
    "wc2022": ("FIFA World Cup", {2022}),
    "euro2016": ("UEFA Euro", {2016}),
    "euro2021": ("UEFA Euro", {2021}),
    "euro2024": ("UEFA Euro", {2024}),
}


def _rows(path):
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["home_score"]:
                continue
            yield dict(date=r["date"], home=r["home_team"], away=r["away_team"],
                       hg=int(r["home_score"]), ag=int(r["away_score"]),
                       tournament=r["tournament"],
                       neutral=str(r["neutral"]).strip().upper() == "TRUE")


def load_tournament(path, tournament, years):
    """Warm Elo on ALL matches up to and during the tournament window, then return the
    tournament's matches with pre-match ratings as ``eval_matches``."""
    rows = list(_rows(path))
    annotated = elohist.run_history(rows)
    eval_matches = [m for m in annotated
                    if m["tournament"] == tournament and int(m["date"][:4]) in years]
    return {"eval_matches": eval_matches}
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_calibrate.py::test_load_intl_filters_tournament_and_builds_history -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/datasets.py tests/test_eval_calibrate.py tests/fixtures/eval/intl_results.csv
git commit -m "feat(eval): load past tournaments with self-computed pre-match Elo"
```

## Task 9: calibrate.py — replay, evaluate, sweep + LOTO CV

**Files:**
- Create: `scorito/eval/calibrate.py`
- Test: `tests/test_eval_calibrate.py`

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_eval_calibrate.py
from scorito.eval import calibrate


def _toy_matches():
    # strong home team wins big, even match draws -> a model with sane constants
    # should assign higher P(home) to the first than the second.
    return [
        dict(home="A", away="B", hg=3, ag=0, home_pre=1900, away_pre=1500, neutral=True),
        dict(home="C", away="D", hg=1, ag=1, home_pre=1600, away_pre=1600, neutral=True),
    ]


def test_evaluate_returns_logloss_and_brier():
    res = calibrate.evaluate(_toy_matches(),
                             dict(rho=0.001, total=2.6, divisor=250.0))
    assert "logloss_1x2" in res and res["logloss_1x2"] > 0
    assert 0 <= res["brier_1x2"] <= 2


def test_sweep_picks_lower_logloss():
    matches = _toy_matches()
    grids = dict(rho=[0.001], total=[2.6], divisor=[150.0, 400.0])
    best = calibrate.sweep({"toy": matches}, grids)
    assert best["divisor"] in (150.0, 400.0)
    assert "cv_logloss" in best
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_eval_calibrate.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# scorito/eval/calibrate.py
"""Replay past tournaments through the Elo->grid model, score calibration, and sweep
the three tunable constants under leave-one-tournament-out cross-validation."""
import itertools

from scorito.eval import metrics
from scorito.model.goals import goals_from_elo
from scorito.model.grid import build_grid


def _predict(match, c):
    lam1, lam2 = goals_from_elo(match["home_pre"], match["away_pre"], total=c["total"])
    # goals_from_elo uses config.ELO_GOAL_DIVISOR internally; pass override via supremacy:
    g = build_grid(lam1, lam2, rho=c["rho"])
    return [g.p_home, g.p_draw, g.p_away], g


def _outcome_idx(hg, ag):
    return 0 if hg > ag else (1 if hg == ag else 2)


def evaluate(matches, c):
    ll = br = 0.0
    rel = []
    for m in matches:
        probs, _ = _predict(m, c)
        idx = _outcome_idx(m["hg"], m["ag"])
        ll += metrics.log_loss(probs, idx)
        br += metrics.brier(probs, idx)
        rel.append((probs[0], idx == 0))
    n = max(1, len(matches))
    return {"logloss_1x2": ll / n, "brier_1x2": br / n,
            "reliability": metrics.reliability_bins(rel), "n": len(matches)}


def _grid_best(datasets, grids):
    """Constants minimising mean per-tournament 1X2 log-loss over ``datasets``."""
    best = None
    for rho, total, divisor in itertools.product(grids["rho"], grids["total"], grids["divisor"]):
        c = dict(rho=rho, total=total, divisor=divisor)
        ll = sum(evaluate(datasets[lab], c)["logloss_1x2"] for lab in datasets) / len(datasets)
        if best is None or ll < best["logloss"]:
            best = dict(c, logloss=ll)
    return best


def sweep(datasets, grids):
    """Grid-best constants on ALL data, plus an HONEST out-of-sample ``cv_logloss`` from
    leave-one-tournament-out CV: for each fold the grid is re-fit on the *other*
    tournaments and scored on the held-out one. (Single tournament -> degenerates to
    in-sample.)"""
    labels = list(datasets)
    per_fold = {}
    for held in labels:
        train = {k: v for k, v in datasets.items() if k != held} or datasets
        bt = _grid_best(train, grids)
        c = dict(rho=bt["rho"], total=bt["total"], divisor=bt["divisor"])
        per_fold[held] = evaluate(datasets[held], c)["logloss_1x2"]
    final = _grid_best(datasets, grids)
    return dict(rho=final["rho"], total=final["total"], divisor=final["divisor"],
                cv_logloss=sum(per_fold.values()) / len(per_fold), per_fold=per_fold)
```

> NOTE: `goals_from_elo` reads `config.ELO_GOAL_DIVISOR` internally. To make `divisor`
> sweepable, Step 3a refactors `goals_from_elo(elo_home, elo_away, total=..., divisor=config.ELO_GOAL_DIVISOR)`
> to accept an override (default preserves current behaviour). Update the call in
> `scorito/main.py`/`goals.expected_goals` is unchanged (uses default).

- [ ] **Step 3a: Refactor goals_from_elo to accept divisor override**

```python
# scorito/model/goals.py  — change signature + body
def goals_from_elo(elo_home, elo_away, total=config.NEUTRAL_AVG_TOTAL,
                   divisor=config.ELO_GOAL_DIVISOR):
    sup = (elo_home - elo_away) / divisor
    lam1 = max(_FLOOR, (total + sup) / 2.0)
    lam2 = max(_FLOOR, (total - sup) / 2.0)
    return lam1, lam2
```
Then in `calibrate._predict`, pass `divisor=c["divisor"]`:
```python
    lam1, lam2 = goals_from_elo(match["home_pre"], match["away_pre"],
                                total=c["total"], divisor=c["divisor"])
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_eval_calibrate.py tests/test_goals.py -q`
Expected: PASS (new calibrate tests + existing goals tests still green).

- [ ] **Step 5: Commit**

```bash
git add scorito/eval/calibrate.py scorito/model/goals.py tests/test_eval_calibrate.py
git commit -m "feat(eval): calibration replay + constant sweep with LOTO CV"
```

## Task 10: calibrate CLI + optional config write

**Files:**
- Modify: `scorito/eval/__main__.py`
- Test: manual smoke

- [ ] **Step 1: Add the `calibrate` subcommand**

```python
# add to scorito/eval/__main__.py
from scorito.eval import calibrate as cal
from scorito.eval import datasets as ds
from scorito import config as cfg


def _calibrate(args):
    labels = args.tournaments.split(",") if args.tournaments else list(ds.TOURNAMENTS)
    data = {}
    for lab in labels:
        tour, years = ds.TOURNAMENTS[lab]
        data[lab] = ds.load_tournament(args.results_csv, tour, years)["eval_matches"]
    grids = dict(rho=[0.0, 0.001, 0.01], total=[2.4, 2.6, 2.8],
                 divisor=[150.0, 200.0, 250.0, 300.0, 400.0])
    current = dict(rho=cfg.DC_RHO, total=cfg.NEUTRAL_AVG_TOTAL, divisor=cfg.ELO_GOAL_DIVISOR)
    base = cal.sweep({k: v for k, v in data.items()},
                     {k: [current[k]] for k in current})
    best = cal.sweep(data, grids)
    print(f"current  cv_logloss={base['cv_logloss']:.4f}  {current}")
    print(f"optimal  cv_logloss={best['cv_logloss']:.4f}  "
          f"rho={best['rho']} total={best['total']} divisor={best['divisor']}")
    print(f"per-fold: {best['per_fold']}")
    if args.write:
        _write_constants(best)
        print("Wrote DC_RHO / NEUTRAL_AVG_TOTAL / ELO_GOAL_DIVISOR to config.py")


def _write_constants(best):
    import re
    path = "scorito/config.py"
    txt = open(path, encoding="utf-8").read()
    txt = re.sub(r"DC_RHO = [\d.]+", f"DC_RHO = {best['rho']}", txt)
    txt = re.sub(r"NEUTRAL_AVG_TOTAL = [\d.]+", f"NEUTRAL_AVG_TOTAL = {best['total']}", txt)
    txt = re.sub(r"ELO_GOAL_DIVISOR = [\d.]+", f"ELO_GOAL_DIVISOR = {best['divisor']}", txt)
    open(path, "w", encoding="utf-8").write(txt)
```
Wire it into `main()`:
```python
    c = sub.add_parser("calibrate")
    c.add_argument("--results-csv", default="data/cache/history/intl_results.csv")
    c.add_argument("--tournaments", default="")
    c.add_argument("--write", action="store_true")
    c.set_defaults(func=_calibrate)
```

- [ ] **Step 2: Smoke test (after caching the CSV)**

Run: `.venv/bin/python -m scorito.eval calibrate --results-csv tests/fixtures/eval/intl_results.csv --tournaments wc2018`
Expected: prints current vs optimal cv_logloss without error.

- [ ] **Step 3: Commit**

```bash
git add scorito/eval/__main__.py
git commit -m "feat(eval): calibrate CLI with optional --write to config"
```

## Task 11: docs + full suite

- [ ] **Step 1:** Add a `## Validation` section to `README.md` documenting both commands.
- [ ] **Step 2:** Run the whole suite.

Run: `.venv/bin/python -m pytest -q`
Expected: all pass (existing 46 + new eval tests).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the eval harness (scorecard + calibrate)"
```

---

## Self-Review

- **Spec coverage:** metrics §6 → Tasks 1–2; calibrate §7 → Tasks 7–10; scorecard §8 → Tasks 3–6; CLI §9 → Tasks 6,10; error handling §10 → Tasks 3 (skip unplayed), 5 (missing scorers), 8 (default Elo via `dict.get`); testing §11 → every task is TDD. Data sources §5 refined (martj42 CSV + self-Elo) — flagged at top.
- **Placeholders:** none — every code step is complete and runnable.
- **Type consistency:** `load_picks` returns `{scorelines, standings, champion, topscorers}` consumed verbatim by `__main__._scorecard`; `eval_matches` dict keys (`home/away/hg/ag/home_pre/away_pre/neutral`) produced by `datasets`/`elohist` and consumed by `calibrate._predict`/`evaluate`; `goals_from_elo` override is backward-compatible (defaults unchanged).
- **Open risk:** martj42 CSV header is verified on first fetch (Task 8 note); team-name spelling between that CSV and openfootball differs but only matters for the historical Elo backtest (self-contained), not the live model.
