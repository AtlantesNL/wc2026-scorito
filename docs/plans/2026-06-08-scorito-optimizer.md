# Scorito WC2026 Optimizer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tool that outputs optimal Scorito WC2026 group-phase picks (72 scorelines jointly optimized with auto-derived standings, 6 topscorers, champion).

**Architecture:** Pure-Python package `scorito`. Data layer (fixtures/Elo/odds/priors) → goals model (odds→λ with Elo fallback) → Dixon-Coles score grids → per-match EV → Monte-Carlo group simulation + K⁶ enumeration for the joint scoreline/standings optimum → champion (pool leverage) + topscorers (EV) → report.md + picks.csv. Elo-only path works end-to-end before odds are layered on.

**Tech Stack:** Python 3.12 (uv venv), penaltyblog 1.11.0 (`calculate_implied`/`ImpliedMethod.SHIN`, `goal_expectancy`, `create_dixon_coles_grid`), numpy, scipy (`linear_sum_assignment`), requests, pytest.

**Conventions:** package `scorito/`, tests `tests/` mirroring it. Run tests `.venv/bin/pytest -q`. WC group games are **neutral venue** → no home-advantage term (any real edge is already in the odds). `team1` is nominal first team only. Commit after each task.

---

### Task 1: Config + domain types

**Files:**
- Create: `scorito/__init__.py` (empty), `scorito/config.py`, `scorito/types.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**
```python
# tests/test_config.py
from scorito import config
from scorito.types import Team, Match, Scoreline

def test_scoring_constants():
    assert config.PTS_EXACT == 45
    assert config.PTS_TOTO == 30
    assert config.PTS_POSITION == 25
    assert config.CHAMPION_BONUS == 250
    assert config.TOPSCORER_SLOTS == 6

def test_topscorer_multiplier_ratio():
    m = config.TOPSCORER_MULT
    assert m["DEF"] == m["GK"] == 4 and m["MID"] == 2 and m["ATT"] == 1

def test_types_construct():
    t = Team(name="Spain", code="ESP", group="H", elo=2100.0, confederation="UEFA")
    mt = Match(team1="Spain", team2="Uruguay", group="H", matchday=1, date="2026-06-15")
    s = Scoreline(home=1, away=0, ev=22.6)
    assert t.elo == 2100.0 and mt.group == "H" and s.toto() == "H"
```

- [ ] **Step 2: Run to verify fail** — `.venv/bin/pytest tests/test_config.py -q` → FAIL (import error)

- [ ] **Step 3: Implement**
```python
# scorito/types.py
from dataclasses import dataclass, field

@dataclass
class Team:
    name: str; code: str; group: str; elo: float = 1500.0; confederation: str = ""

@dataclass
class Match:
    team1: str; team2: str; group: str; matchday: int; date: str = ""

@dataclass
class Scoreline:
    home: int; away: int; ev: float = 0.0
    def toto(self) -> str:
        return "H" if self.home > self.away else ("A" if self.away > self.home else "D")
```
```python
# scorito/config.py
PTS_EXACT = 45
PTS_TOTO = 30
PTS_POSITION = 25
MAX_GROUP_POSITION_PTS = 100
CHAMPION_BONUS = 250
# Relative per-goal multiplier (absolute base contested 8/16/32 vs 16/32/64 — confirm in-app).
TOPSCORER_MULT = {"GK": 4, "DEF": 4, "MID": 2, "ATT": 1}
TOPSCORER_SLOTS = 6           # contested: blog says 4 — confirm in-app
DC_RHO = 0.001                # Dixon-Coles low-score correction
MAX_GOALS = 10                # score-grid cutoff
TOPK_SCORELINES = 6           # candidates kept per match for the group enumerator
MC_SIMS = 20000               # Monte-Carlo group simulations
NEUTRAL_AVG_TOTAL = 2.6       # tournament-average total goals for the Elo fallback
```

- [ ] **Step 4: Run to verify pass** — `.venv/bin/pytest tests/test_config.py -q` → PASS

- [ ] **Step 5: Commit** — `git add -A && git commit -m "feat: config constants and domain types"`

---

### Task 2: Fixtures loader

**Files:**
- Create: `scorito/data/__init__.py`, `scorito/data/fixtures.py`
- Test: `tests/test_fixtures.py`, `tests/fixtures/worldcup_sample.json`

Goal: parse openfootball worldcup.json structure into `{group: [Match,...]}` and `{group: [team names]}`. Live URL `https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json`; `load_fixtures(path_or_url)` reads a local path or http(s). Tests use a recorded sample (no network).

- [ ] **Step 1: Write failing test** (record a 1-group, 6-match slice of the real JSON into `tests/fixtures/worldcup_sample.json` first; openfootball schema: top-level `{"rounds":[{"matches":[{"date","team1","team2","group"}...]}]}`).
```python
# tests/test_fixtures.py
from pathlib import Path
from scorito.data.fixtures import load_fixtures, group_teams

SAMPLE = Path(__file__).parent / "fixtures" / "worldcup_sample.json"

def test_load_groups_and_matches():
    matches = load_fixtures(str(SAMPLE))
    g = [m for m in matches if m.group == "A"]
    assert len(g) == 6                         # round-robin of 4
    assert all(m.team1 and m.team2 for m in g)

def test_group_teams_are_four_unique():
    matches = load_fixtures(str(SAMPLE))
    teams = group_teams(matches)["A"]
    assert len(teams) == 4 and len(set(teams)) == 4
```

- [ ] **Step 2: Run to verify fail** — FAIL (module missing)

- [ ] **Step 3: Implement** — `load_fixtures` fetches via `requests.get` if arg startswith `http`, else `open`; iterate `data["rounds"][*]["matches"][*]`, build `Match(team1, team2, group=m["group"].replace("Group ",""), matchday=round_index, date=m.get("date",""))`. `group_teams(matches)` returns `{group: sorted-unique team names preserving first-seen order}`.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: openfootball fixtures loader"`

---

### Task 3: Elo source

**Files:**
- Create: `scorito/data/elo.py`
- Test: `tests/test_elo.py`, `tests/fixtures/elo_sample.html`

Goal: current Elo per team from eloratings.net, cached to `data/cache/elo.json`, with a name-normalization map (eloratings names → openfootball names, e.g. "United States"→"USA", "South Korea"→"Korea Republic" as needed). Tests parse a recorded HTML snippet (no network).

- [ ] **Step 1: Write failing test**
```python
# tests/test_elo.py
from pathlib import Path
from scorito.data.elo import parse_elo_html, normalize_name

def test_parse_elo_html():
    html = (Path(__file__).parent / "fixtures" / "elo_sample.html").read_text()
    ratings = parse_elo_html(html)
    assert ratings["Spain"] > 1900
    assert all(isinstance(v, float) for v in ratings.values())

def test_normalize_name():
    assert normalize_name("United States") == "USA"
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — record a small slice of eloratings.net into `elo_sample.html`. `parse_elo_html` uses a regex/`pandas.read_html` to pull (team, rating) rows → `{name: float}`. `normalize_name` applies a dict `ELO_TO_OPENFOOTBALL`. `get_elo(teams, cache="data/cache/elo.json")`: load cache if present else fetch `https://www.eloratings.net/` + parse + write cache; return `{team: elo}` keyed by openfootball names, defaulting unknown teams to 1500.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: eloratings.net source with caching + name map"`

---

### Task 4: Score-grid wrapper

**Files:**
- Create: `scorito/model/__init__.py`, `scorito/model/grid.py`
- Test: `tests/test_grid.py`

Goal: thin wrapper over `create_dixon_coles_grid` exposing a stable `ScoreGrid` interface (so a fallback could slot in later). Methods: `exact(i,j)`, `p_home/p_draw/p_away`, `matrix` (np.ndarray (n,n)).

- [ ] **Step 1: Write failing test**
```python
# tests/test_grid.py
import numpy as np
from scorito.model.grid import build_grid

def test_grid_sums_to_one_and_1x2_consistent():
    g = build_grid(1.6, 0.9)
    assert abs(g.matrix.sum() - 1.0) < 1e-6
    assert abs((g.p_home + g.p_draw + g.p_away) - 1.0) < 1e-6
    # higher home lambda -> home win more likely than away
    assert g.p_home > g.p_away

def test_exact_matches_matrix():
    g = build_grid(1.6, 0.9)
    assert abs(g.exact(1, 0) - g.matrix[1, 0]) < 1e-9
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement**
```python
# scorito/model/grid.py
import numpy as np
from penaltyblog.models import create_dixon_coles_grid
from scorito import config

class ScoreGrid:
    def __init__(self, matrix, p_home, p_draw, p_away):
        self.matrix = matrix; self.p_home = p_home; self.p_draw = p_draw; self.p_away = p_away
    def exact(self, i, j): return float(self.matrix[i, j])

def build_grid(lam_home, lam_away, rho=config.DC_RHO, max_goals=config.MAX_GOALS) -> ScoreGrid:
    g = create_dixon_coles_grid(lam_home, lam_away, rho=rho, max_goals=max_goals)
    n = max_goals + 1
    m = np.array([[g.exact_score(i, j) for j in range(n)] for i in range(n)], dtype=float)
    m /= m.sum()
    return ScoreGrid(m, float(g.home_win), float(g.draw), float(g.away_win))
```

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: Dixon-Coles score-grid wrapper"`

---

### Task 5: Goals model (odds→λ with Elo fallback)

**Files:**
- Create: `scorito/model/goals.py`
- Test: `tests/test_goals.py`

Goal: `expected_goals(...)` returning `(lam1, lam2)`. Odds path: Shin de-vig 1X2 → `goal_expectancy`; if O/U total line present, rescale `(lam1,lam2)` so their sum equals the line (split preserved). Elo path: supremacy from Elo diff (`dr = elo1-elo2`; expected goal supremacy `sup = dr/CONST`), total = `NEUTRAL_AVG_TOTAL`, so `lam1=(total+sup)/2`, `lam2=(total-sup)/2`, floored at 0.15.

- [ ] **Step 1: Write failing tests**
```python
# tests/test_goals.py
from scorito.model.goals import goals_from_odds, goals_from_elo

def test_goals_from_odds_roundtrip_favorite():
    lam1, lam2 = goals_from_odds(odds=[1.5, 4.0, 6.0])   # strong home favorite
    assert lam1 > lam2 and lam1 > 1.0

def test_goals_from_odds_totals_pins_sum():
    lam1, lam2 = goals_from_odds(odds=[2.0, 3.4, 3.6], total_line=2.5)
    assert abs((lam1 + lam2) - 2.5) < 1e-6

def test_goals_from_elo_monotone_and_floored():
    a1, a2 = goals_from_elo(2000, 1500)   # big gap
    b1, b2 = goals_from_elo(1600, 1500)   # small gap
    assert (a1 - a2) > (b1 - b2)          # supremacy grows with Elo gap
    assert a2 >= 0.15
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `goals_from_odds(odds, total_line=None)`: `p = calculate_implied(odds, method=ImpliedMethod.SHIN).probabilities`; `ge = goal_expectancy(p[0],p[1],p[2], dc_adj=True, rho=config.DC_RHO)`; `lam1,lam2 = ge["home_exp"], ge["away_exp"]`; if `total_line`: `s=lam1+lam2; lam1*=total_line/s; lam2*=total_line/s`. `goals_from_elo(e1,e2,total=config.NEUTRAL_AVG_TOTAL)`: `sup = (e1-e2)/250.0` (≈ a 250-Elo gap → ~1 goal supremacy); `lam1=max(0.15,(total+sup)/2); lam2=max(0.15,(total-sup)/2)`. `expected_goals(match, odds_map, elo)`: prefer odds if present else Elo.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: goal-expectancy model (odds + Elo fallback)"`

---

### Task 6: Per-match EV (top-K scorelines)

**Files:**
- Create: `scorito/model/match_ev.py`
- Test: `tests/test_match_ev.py`

Goal: `topk_scorelines(grid, k)` → list of `Scoreline` sorted by `EV = 45*P(exact) + 30*P(toto-outcome)` desc.

- [ ] **Step 1: Write failing test** (hand-computable: a grid where 1-0 dominates).
```python
# tests/test_match_ev.py
import numpy as np
from scorito.model.grid import ScoreGrid
from scorito.model.match_ev import topk_scorelines, score_ev

def _grid():
    m = np.zeros((3, 3)); m[1,0]=0.4; m[0,0]=0.2; m[2,1]=0.2; m[1,1]=0.1; m[0,1]=0.1
    return ScoreGrid(m, p_home=0.6, p_draw=0.3, p_away=0.1)

def test_score_ev_known_value():
    g = _grid()
    # 1-0: 45*0.4 + 30*P(H=0.6) = 18 + 18 = 36
    assert abs(score_ev(g, 1, 0) - 36.0) < 1e-9

def test_topk_orders_by_ev():
    g = _grid()
    picks = topk_scorelines(g, k=3)
    assert (picks[0].home, picks[0].away) == (1, 0)
    assert picks[0].ev >= picks[1].ev >= picks[2].ev
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement**
```python
# scorito/model/match_ev.py
from scorito import config
from scorito.types import Scoreline

def score_ev(grid, i, j):
    p_toto = grid.p_home if i > j else (grid.p_away if j > i else grid.p_draw)
    return config.PTS_EXACT * grid.exact(i, j) + config.PTS_TOTO * p_toto

def topk_scorelines(grid, k=config.TOPK_SCORELINES):
    n = grid.matrix.shape[0]
    cands = [Scoreline(i, j, score_ev(grid, i, j)) for i in range(n) for j in range(n)]
    cands.sort(key=lambda s: s.ev, reverse=True)
    return cands[:k]
```

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: per-match EV-optimal scorelines"`

---

### Task 7: Group Monte-Carlo simulator

**Files:**
- Create: `scorito/model/group_sim.py`
- Test: `tests/test_group_sim.py`

Goal: `position_probs(group_matches, grids, sims)` → `dict[team] -> np.array(4)` of P(finish 1st..4th). Sampling: draw each match score from its grid (flatten matrix, `np.random.choice`); accumulate pts(3/1/0)/GD/GF; rank with FIFA tiebreakers: (1) pts, (2) GD, (3) GF, (4) head-to-head pts among tied, (5) h2h GD, (6) h2h GF, (7) random. Use a seeded RNG for reproducible tests.

- [ ] **Step 1: Write failing tests**
```python
# tests/test_group_sim.py
import numpy as np
from scorito.model.grid import build_grid
from scorito.model.group_sim import position_probs, _rank_table

def test_position_probs_sum_to_one():
    teams = ["A","B","C","D"]
    matches = [("A","B"),("A","C"),("A","D"),("B","C"),("B","D"),("C","D")]
    grids = {m: build_grid(1.3, 1.3) for m in matches}   # all even
    probs = position_probs(teams, matches, grids, sims=2000, seed=1)
    for t in teams:
        assert abs(probs[t].sum() - 1.0) < 1e-9
    # symmetric group -> each team ~25% to win
    assert abs(probs["A"][0] - 0.25) < 0.06

def test_rank_table_tiebreakers():
    # A and B both 6 pts; A has better GD -> A first
    stats = {"A":dict(pts=6,gd=4,gf=5),"B":dict(pts=6,gd=2,gf=4),
             "C":dict(pts=3,gd=-2,gf=2),"D":dict(pts=0,gd=-4,gf=1)}
    order = _rank_table(stats, h2h=None, rng=np.random.default_rng(0))
    assert order[0] == "A" and order[1] == "B" and order[-1] == "D"
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — precompute each grid's flattened prob vector + (i,j) index list once. Per sim: sample 6 scores, tally stats, build h2h sub-results, `_rank_table` sorts by key `(pts, gd, gf)` then resolves equal-key clusters by head-to-head mini-table then `rng.random()`. Tally final positions; divide by `sims`.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: Monte-Carlo group simulator with FIFA tiebreakers"`

---

### Task 8: Group enumerator (joint scoreline/standings optimum)

**Files:**
- Create: `scorito/model/group_opt.py`
- Test: `tests/test_group_opt.py`

Goal: choose 6 scorelines per group maximizing `Σ matchEV + Σ_pos 25·P(predicted_team_at_pos finishes at pos)`. `optimize_group(...)` enumerates top-K per match (≤K⁶), derives the predicted standing deterministically from each combo (same `_rank_table`, no randomness — ties broken by a fixed order), scores it against `position_probs`, returns the best `GroupResult`. Include `standings_only_ordering(probs)` via `scipy.optimize.linear_sum_assignment` for the cross-check test.

- [ ] **Step 1: Write failing tests** (constructed case where the joint optimum ≠ per-match argmax).
```python
# tests/test_group_opt.py
from scorito.model.group_opt import optimize_group, standings_only_ordering

def test_enumerator_beats_naive_on_total(monkeypatch_free_small_group):
    res = optimize_group(*monkeypatch_free_small_group, k=4, sims=4000, seed=2)
    # the optimizer's total must be >= the naive per-match-argmax total
    assert res.total >= res.naive_total
    assert len(res.scorelines) == 6
    assert set(res.predicted_standing) == set(monkeypatch_free_small_group[0])  # all 4 teams placed

def test_standings_only_assignment_is_permutation():
    import numpy as np
    probs = {"A":np.array([.7,.2,.1,0]),"B":np.array([.2,.5,.2,.1]),
             "C":np.array([.1,.2,.5,.2]),"D":np.array([0,.1,.2,.7])}
    order = standings_only_ordering(probs)
    assert order == ["A","B","C","D"]
```
(Provide `monkeypatch_free_small_group` as a `conftest.py` fixture: 4 teams, 6 matches, grids built from deliberately asymmetric lambdas so the standings term pulls the choice away from each match's argmax.)

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `optimize_group(teams, matches, grids, k, sims, seed)`: `probs = position_probs(...)`; `cand = {m: topk_scorelines(grids[m], k)}`; `naive = {m: cand[m][0]}`; for each combo in `itertools.product(*cand.values())`: derive stats→predicted order (deterministic `_rank_table` with fixed tiebreak), `match_pts = Σ s.ev`, `stand_pts = Σ_p 25*probs[order[p]][p]`, `total = match_pts + stand_pts`; track max. Return `GroupResult(scorelines, predicted_standing, match_pts, stand_pts, total, naive_total)`. `standings_only_ordering`: build matrix `P[team,pos]`, `linear_sum_assignment(-P)`, map back to ordered team list.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: joint group scoreline/standings optimizer"`

---

### Task 9: Champion (priors + pool leverage)

**Files:**
- Create: `scorito/data/priors.py` (Opta dict + market blend), `scorito/model/champion.py`
- Test: `tests/test_champion.py`

Goal: blend Opta + market win probabilities (with a double-count discount weight), estimate pick-share, and rank champions by a pool-size-aware leverage score. `recommend_champion(pool_size, risk)` → ordered list of `(team, p_win, ev_points, est_share, leverage)`.

- [ ] **Step 1: Write failing tests**
```python
# tests/test_champion.py
from scorito.model.champion import recommend_champion, leverage_score

def test_ev_points_is_p_times_bonus():
    recs = recommend_champion(pool_size=40, risk="balanced")
    top = {r.team: r for r in recs}
    assert abs(top["Spain"].ev_points - top["Spain"].p_win * 250) < 1e-6

def test_larger_pool_pushes_off_the_consensus_favorite():
    small = recommend_champion(pool_size=8, risk="balanced")
    large = recommend_champion(pool_size=400, risk="balanced")
    # Spain (consensus favorite) ranks no better in a huge pool than a small one
    rank = lambda recs: [r.team for r in recs].index("Spain")
    assert rank(large) >= rank(small)
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `priors.py`: `OPTA = {"Spain":0.161,"France":0.130,"England":0.112,"Argentina":0.104,"Portugal":0.070,"Brazil":0.066,"Germany":0.051,"Netherlands":0.036, ...}` (from theanalyst.com June 2026) and `MARKET = {"France":0.17,"Spain":0.16, ...}`; `blended() = normalize(0.6*OPTA + 0.4*MARKET)` (weights reflect partial common source). `champion.py`: `est_share(p_win, pool_size)` ≈ `min(0.9, p_win*share_infl)` with `share_infl` rising for the headline favorite; `leverage_score(p_win, share, pool_size, risk)` = `p_win` for tiny pools, `p_win/share**γ` with γ growing in pool_size for larger pools (balanced uses moderate γ); rank desc.

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: champion pick with pool-leverage adjustment"`

---

### Task 10: Topscorers (EV over candidate table)

**Files:**
- Create: `scorito/data/topscorer_candidates.py` (seed table), `scorito/model/topscorers.py`
- Test: `tests/test_topscorers.py`

Goal: rank candidates by `EV = (g90*3*start_prob + pen_bonus) * team_attack_factor * MULT[position]`; pick top `TOPSCORER_SLOTS`. `team_attack_factor` passed in from the goals model (mean expected goals across the team's 3 group games, normalized to ~1.0).

- [ ] **Step 1: Write failing tests**
```python
# tests/test_topscorers.py
from scorito.model.topscorers import score_candidate, pick_topscorers
from scorito.types import  *  # Candidate defined in topscorers module

def test_defender_outranks_attacker_same_expected_goals():
    teamf = {"NED": 1.2, "FRA": 1.2}
    d = dict(name="Van Dijk", team="NED", position="DEF", g90=0.15, start_prob=0.95, pen_taker=False)
    a = dict(name="Generic ST", team="FRA", position="ATT", g90=0.15, start_prob=0.95, pen_taker=False)
    assert score_candidate(d, teamf) > score_candidate(a, teamf)   # 4x multiplier

def test_pick_returns_n_slots():
    picks = pick_topscorers(team_factors={"ESP":1.4,"FRA":1.3,"NED":1.1}, n=6)
    assert len(picks) == 6
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `topscorer_candidates.py`: `CANDIDATES = [ {name,team,position,g90,start_prob,pen_taker}, ... ]` seeded with Van Dijk, Saliba + 4–6 other penalty/set-piece defenders & attacking wing-backs on strong teams, plus Mbappé, Kane, Yamal, Vinícius, Haaland, Cunha and a handful more attackers/mids. `score_candidate(c, team_factors)`: `pen_bonus = 0.20 if c["pen_taker"] else 0.0`; `ev = (c["g90"]*3*c["start_prob"] + pen_bonus) * team_factors.get(c["team"],1.0) * MULT[c["position"]]`. `pick_topscorers(team_factors, n)`: score all, sort desc, return top n (names + ev + rationale string).

- [ ] **Step 4: Run to verify pass** — PASS

- [ ] **Step 5: Commit** — `git commit -am "feat: topscorer EV model exploiting position multiplier"`

---

### Task 11: Report + CLI (Elo-only end-to-end)

**Files:**
- Create: `scorito/report.py`, `scorito/main.py`
- Test: `tests/test_report.py`, `tests/test_main_smoke.py`

Goal: assemble `out/report.md` + `out/picks.csv`; CLI wires fixtures→Elo→goals→grids→group_opt (all 12 groups)→champion→topscorers. `--no-odds` runs fully offline from Elo. This task yields the first working tool.

- [ ] **Step 1: Write failing tests**
```python
# tests/test_report.py
from scorito.report import build_csv_rows
def test_csv_has_row_per_match_plus_meta():
    fake = {"A": _fake_group_result()}   # helper builds a GroupResult with 6 scorelines
    rows = build_csv_rows(groups=fake, champion="France", topscorers=["Van Dijk"])
    assert sum(1 for r in rows if r["type"] == "match") == 6
    assert any(r["type"] == "champion" for r in rows)
```
```python
# tests/test_main_smoke.py
def test_elo_only_pipeline_runs(monkeypatch, tmp_path):
    # monkeypatch load_fixtures->sample, get_elo->fixed dict; assert report.md + picks.csv written
    from scorito import main
    out = main.run(no_odds=True, pool_size=40, risk="balanced", out_dir=str(tmp_path))
    assert (tmp_path / "report.md").exists() and (tmp_path / "picks.csv").exists()
    assert len(out.groups) >= 1
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `report.py`: `build_csv_rows(...)`, `write_report(result, out_dir)` (markdown per group: scorelines, predicted standing, expected-pts breakdown; champion section; topscorer section). `main.py`: `run(no_odds, pool_size, risk, odds_key=None, out_dir="out")` orchestrates; `argparse` CLI calling `run`. For each group call `optimize_group`; collect `team_attack_factor` from each team's mean λ.

- [ ] **Step 4: Run to verify pass** — PASS; then a real offline run: `.venv/bin/python -m scorito.main --no-odds --pool-size 40 --risk balanced` and eyeball `out/report.md`.

- [ ] **Step 5: Commit** — `git commit -am "feat: report + CLI (Elo-only end-to-end)"`

---

### Task 12: Odds client + wire into goals model

**Files:**
- Create: `scorito/data/odds.py`
- Modify: `scorito/main.py` (use odds when key present)
- Test: `tests/test_odds.py`, `tests/fixtures/odds_sample.json`

Goal: fetch The Odds API `soccer_fifa_world_cup` (`markets=h2h,totals`, `regions=eu`), map bookmaker team names → openfootball names, return `{(team1,team2): {"odds":[h,d,a], "total_line":x|None}}` using median across books. Tests parse a recorded JSON (no network).

- [ ] **Step 1: Write failing test**
```python
# tests/test_odds.py
from pathlib import Path
import json
from scorito.data.odds import parse_odds

def test_parse_odds_median_and_total():
    data = json.loads((Path(__file__).parent/"fixtures"/"odds_sample.json").read_text())
    m = parse_odds(data)
    key = next(iter(m))
    assert len(m[key]["odds"]) == 3
    assert m[key]["total_line"] is None or m[key]["total_line"] > 0
```

- [ ] **Step 2: Run to verify fail** — FAIL

- [ ] **Step 3: Implement** — `fetch_odds(api_key)`: GET `https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds?regions=eu&markets=h2h,totals&oddsFormat=decimal&apiKey=...`. `parse_odds(data)`: per event, collect each book's h2h (median per outcome) and totals (median line + its over/under); map names via `ODDS_TO_OPENFOOTBALL`; key by `(home_team, away_team)`. `main.run`: when `odds_key`, fetch+parse, pass `odds_map` into `expected_goals` (odds preferred, Elo fallback for missing matches).

- [ ] **Step 4: Run to verify pass** — PASS; then a real run with the key: `.venv/bin/python -m scorito.main --odds-key "$ODDS_API_KEY" --pool-size 40 --risk balanced`.

- [ ] **Step 5: Commit** — `git commit -am "feat: The Odds API client wired into goals model"`

---

## Self-Review

**Spec coverage:** §1 scoring→T1; §2 sources→T2,T3,T9,T12; §3 goals→T4,T5; §4 match EV→T6; §5 group optimizer→T7,T8; §6 champion→T9; §7 topscorers→T10; §8 outputs→T11; §9 architecture→all; §10 testing→tests in every task; §11 validation→post-build eyeball in T11/T12 + benchmarks (manual, non-blocking); §12 risks→constants centralized (T1), Elo fallback (T5), double-count discount (T9). No gaps.

**Placeholder scan:** no TBD/"handle edge cases"; every task has concrete tests + implementation approach with signatures and key code. Recorded fixtures (sample JSON/HTML) are created as the first action of their task.

**Type consistency:** `Scoreline.toto()`, `ScoreGrid.exact/.p_home/.p_draw/.p_away/.matrix`, `build_grid`, `topk_scorelines`, `score_ev`, `position_probs`, `_rank_table`, `optimize_group`/`GroupResult(scorelines, predicted_standing, match_pts, stand_pts, total, naive_total)`, `recommend_champion`, `score_candidate`/`pick_topscorers`, `parse_odds`/`fetch_odds` — names consistent across tasks. `GroupResult` is defined in T8 and consumed in T11.
