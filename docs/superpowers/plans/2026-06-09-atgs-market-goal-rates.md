# Anytime-goalscorer market goal rates (③) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Replace hand-estimated `g90` with anytime-goalscorer market goal rates where available (per-match `λ=−ln(1−p)`, summed over a player's group games), blended with the hand estimate as fallback.

**Architecture:** A new ATGS client fetches `player_goal_scorer_anytime` per event and parses it to `{match: {player: price}}`; `build_expected_goals` blends market `λ` (priced) with hand `g90` (unpriced) into a per-candidate `exp_goals`; `score_candidate`/`fame_score`/`sample_player_goals` read `exp_goals` when present (backward compatible). Opt-in via `--atgs`/`--atgs-file`.

**Tech Stack:** Python 3.12, requests, numpy, pytest. No new deps.

---

## Task 1: config (`ATGS_MARGIN`, `ATGS_REGIONS`)

**Files:** Modify `scorito/config.py`, `tests/test_config.py`

- [ ] **Step 1: Failing test** — append to `tests/test_config.py`:
```python
def test_atgs_constants():
    assert config.ATGS_MARGIN > 1.0
    assert "eu" in config.ATGS_REGIONS
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_config.py::test_atgs_constants -q` → FAIL.
- [ ] **Step 3: Implement** — in `scorito/config.py`, after the `SCORELINE_LEVERAGE_GAMMA` line add:
```python
# Anytime-goalscorer (ATGS) market -> goal rates. Flat de-vig (ATGS has no clean complementary leg);
# eu+uk regions for book consensus (~2 credits/event x 72 group games on The Odds API free tier).
ATGS_MARGIN = 1.06
ATGS_REGIONS = "eu,uk"
```
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git add scorito/config.py tests/test_config.py && git commit -m "feat(atgs): config ATGS_MARGIN + ATGS_REGIONS"`

## Task 2: ATGS client (`odds.py`)

**Files:** Modify `scorito/data/odds.py`, `tests/test_odds.py`

- [ ] **Step 1: Failing test** — append to `tests/test_odds.py`:
```python
def test_norm_strips_accents_and_case():
    from scorito.data.odds import _norm
    assert _norm("Kylian Mbappé") == "kylian mbappe"
    assert _norm("João  Félix!") == "joao felix"


def test_parse_atgs_median_across_books_and_name_field():
    from scorito.data.odds import parse_atgs
    raw = [{
        "home_team": "United States", "away_team": "Paraguay",
        "bookmakers": [
            {"key": "b1", "markets": [{"key": "player_goal_scorer_anytime", "outcomes": [
                {"name": "Christian Pulisic", "price": 2.0},
                {"name": "Yes", "description": "Folarin Balogun", "price": 3.0}]}]},
            {"key": "b2", "markets": [{"key": "player_goal_scorer_anytime", "outcomes": [
                {"name": "Christian Pulisic", "price": 2.4},
                {"name": "No", "description": "Folarin Balogun", "price": 1.4}]}]},
        ],
    }]
    m = parse_atgs(raw)
    sel = m[("USA", "Paraguay")]
    assert abs(sel["christian pulisic"] - 2.2) < 1e-9     # median(2.0, 2.4)
    assert sel["folarin balogun"] == 3.0                   # "Yes" leg via description; "No" skipped
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_odds.py -q` → FAIL (no `_norm`/`parse_atgs`).
- [ ] **Step 3: Implement** — in `scorito/data/odds.py`: add `import unicodedata` and `from scorito import config` at the top (next to `import statistics`), then append:
```python
EVENTS_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events"
EVENT_ODDS_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events/{eid}/odds"

# Our-candidate-name -> the name The Odds API lists, for the few that don't normalize-match.
# Populate during the real run once the feed's spellings are known.
ATGS_PLAYER_ALIASES = {}


def _norm(name: str) -> str:
    """Casefold + strip accents/punctuation for player-name matching across sources."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def fetch_atgs(api_key, regions=None):
    """List WC events, then pull player_goal_scorer_anytime per event. Returns a list of per-event
    /odds JSON responses (cache it; replay via --atgs-file). Failed events are skipped."""
    regions = regions or config.ATGS_REGIONS
    ev = requests.get(EVENTS_URL, params=dict(apiKey=api_key), timeout=30)
    ev.raise_for_status()
    out = []
    for e in ev.json():
        try:
            r = requests.get(EVENT_ODDS_URL.format(eid=e["id"]),
                             params=dict(regions=regions, markets="player_goal_scorer_anytime",
                                         oddsFormat="decimal", apiKey=api_key), timeout=30)
            r.raise_for_status()
            out.append(r.json())
        except requests.RequestException:
            continue
    return out


def parse_atgs(raw):
    """``raw``: list of per-event /odds responses. -> ``{(home_ofb, away_ofb): {norm_player: median_price}}``."""
    out = {}
    for ev in raw:
        key = (_ofb(ev["home_team"]), _ofb(ev["away_team"]))
        prices = {}
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk.get("key") != "player_goal_scorer_anytime":
                    continue
                for o in mk.get("outcomes", []):
                    if o.get("name") in ("No", "Under"):       # negative leg
                        continue
                    player = o.get("description") or o.get("name", "")
                    if player in ("", "Yes", "No", "Over", "Under"):
                        continue
                    prices.setdefault(_norm(player), []).append(o["price"])
        if prices:
            out[key] = {p: statistics.median(v) for p, v in prices.items()}
    return out
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_odds.py -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/data/odds.py tests/test_odds.py && git commit -m "feat(atgs): The Odds API anytime-goalscorer client + parser + name-norm"`

## Task 3: market→λ blend + wire-through (`topscorers.py`)

**Files:** Modify `scorito/model/topscorers.py`, `tests/test_topscorers.py`

- [ ] **Step 1: Failing test** — append to `tests/test_topscorers.py`:
```python
def test_build_expected_goals_market_blend_and_backcompat():
    import math
    from types import SimpleNamespace
    from scorito.model.topscorers import build_expected_goals, score_candidate, fame_score
    matches = [SimpleNamespace(team1="USA", team2="Paraguay"),
               SimpleNamespace(team1="USA", team2="Uruguay"),
               SimpleNamespace(team1="Wales", team2="USA")]
    tf = {"USA": 1.0}
    cand = dict(name="Christian Pulisic", team="USA", position="ATT", g90=0.47, start_prob=0.9)
    # priced in match 1 only -> blend (market match 1 + hand matches 2,3)
    atgs = {("USA", "Paraguay"): {"christian pulisic": 2.5}}        # p=(1/2.5)/1.06=0.377 -> lam=0.474
    out = build_expected_goals([cand], matches, atgs, tf, margin=1.06)[0]
    p = (1 / 2.5) / 1.06
    expected = -math.log(1 - p) + 2 * (0.47 * 0.9 * 1.0)            # 1 market + 2 hand matches
    assert abs(out["exp_goals"] - expected) < 1e-6
    assert out["goals_src"] == "blend"
    assert abs(score_candidate(out, tf) - out["exp_goals"] * 8) < 1e-9   # ATT mult, no team_factor re-applied
    # backward compat: a candidate without exp_goals uses the g90 path unchanged
    assert abs(score_candidate(cand, tf) - (0.47 * 3 * 0.9) * 1.0 * 8) < 1e-9
    assert abs(fame_score(out, tf) - out["exp_goals"]) < 1e-9
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_topscorers.py::test_build_expected_goals_market_blend_and_backcompat -q` → FAIL.
- [ ] **Step 3a: Implement `build_expected_goals`** — in `scorito/model/topscorers.py` add `import math` at the top and `from scorito.data.odds import _norm, ATGS_PLAYER_ALIASES` (below the existing imports), then append:
```python
def _atgs_lambda(price, margin):
    """ATGS price -> per-match goal rate. p=(1/price)/margin de-vigged; lambda=-ln(1-p)."""
    p = min(0.99, (1.0 / price) / margin)
    return -math.log(1.0 - p)


def build_expected_goals(candidates, matches, atgs_map, team_factors, margin=config.ATGS_MARGIN):
    """Augment each candidate with ``exp_goals`` (expected group goals) + ``goals_src``: market lambda
    (-ln(1-p), includes pens+opponent -> no team_factor/pen re-applied) where the player is priced for
    that group match, else the hand g90 fallback. Order-agnostic match lookup."""
    out = []
    for c in candidates:
        cms = [(m.team1, m.team2) for m in matches if c["team"] in (m.team1, m.team2)]
        pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
        n = max(1, len(cms))
        key = _norm(ATGS_PLAYER_ALIASES.get(c["name"], c["name"]))
        total, n_mkt = 0.0, 0
        for (h, a) in cms:
            sel = atgs_map.get((h, a)) or atgs_map.get((a, h)) or {}
            price = sel.get(key)
            if price and price > 1.0:
                total += _atgs_lambda(price, margin)
                n_mkt += 1
            else:
                total += c["g90"] * c["start_prob"] * team_factors.get(c["team"], 1.0) \
                    + PEN_BONUS * pen_share / n
        src = "market" if cms and n_mkt == len(cms) else ("hand" if n_mkt == 0 else "blend")
        out.append(dict(c, exp_goals=total, goals_src=src))
    return out
```
- [ ] **Step 3b: Wire `exp_goals` into the three consumers** — replace `score_candidate`, `fame_score`, and `sample_player_goals` in `scorito/model/topscorers.py` with:
```python
def score_candidate(c, team_factors) -> float:
    if "exp_goals" in c:
        return c["exp_goals"] * config.TOPSCORER_MULT[c["position"]]
    pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
    expected_goals = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
    return expected_goals * team_factors.get(c["team"], 1.0) * config.TOPSCORER_MULT[c["position"]]


def fame_score(c, team_factors) -> float:
    """Rival-ownership weight: expected group goals WITHOUT the position multiplier."""
    if "exp_goals" in c:
        return c["exp_goals"]
    pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
    expected_goals = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
    return expected_goals * team_factors.get(c["team"], 1.0)
```
and in `sample_player_goals`, replace the per-candidate lambda computation
(`exp = ...; lam = max(0.0, exp * team_factors...)`) with:
```python
        if "exp_goals" in c:
            lam = max(0.0, c["exp_goals"])
        else:
            pen_share = c.get("pen_share", 1.0 if c.get("pen_taker") else 0.0)
            exp = c["g90"] * 3 * c["start_prob"] + PEN_BONUS * pen_share
            lam = max(0.0, exp * team_factors.get(c["team"], 1.0))
        out[c["name"]] = rng.poisson(lam, size=sims)
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_topscorers.py -q` → PASS (new test + the existing 6 unchanged).
- [ ] **Step 5: Commit** `git add scorito/model/topscorers.py tests/test_topscorers.py && git commit -m "feat(atgs): build_expected_goals market->lambda blend; consumers read exp_goals"`

## Task 4: CLI + wiring + report (`main.py`, `report.py`)

**Files:** Modify `scorito/main.py`, `scorito/report.py`

- [ ] **Step 1: `run` signature + ATGS map** — in `scorito/main.py` change the `run(...)` signature to add `atgs=False, atgs_file=None` (after `odds_file=None`), and after the `odds_map`/`used_odds` block insert:
```python
    atgs_map = {}
    if atgs_file or (atgs and odds_key):
        from scorito.data import odds as odds_mod
        if atgs_file:
            atgs_raw = json.load(open(atgs_file, encoding="utf-8"))
        else:
            atgs_raw = odds_mod.fetch_atgs(odds_key)
            os.makedirs("data/cache", exist_ok=True)
            with open("data/cache/atgs_raw.json", "w", encoding="utf-8") as f:
                json.dump(atgs_raw, f)
        atgs_map = odds_mod.parse_atgs(atgs_raw)
```
- [ ] **Step 2: Augment `kept`** — in `scorito/main.py`, add `build_expected_goals` to the topscorers import
(`from scorito.model.topscorers import build_expected_goals, pick_topscorers`), then immediately after the
`kept, dropped = squads_data.validate_candidates(CANDIDATES, squads)` line add:
```python
    if atgs_map:
        kept = build_expected_goals(kept, matches, atgs_map, team_factors)
```
- [ ] **Step 3: argparse + call** — in `main(argv=None)` add after the `--odds-file` argument:
```python
    p.add_argument("--atgs", action="store_true", help="also pull anytime-goalscorer odds (needs --odds-key)")
    p.add_argument("--atgs-file", default=None, help="load a saved ATGS JSON instead of fetching")
```
and pass them to `run(...)`: add `atgs=args.atgs, atgs_file=args.atgs_file` to the `run(` call, and change
the `no_odds` guard line so an ATGS file run still computes (no change needed if `--odds-file`/`--odds-key`
also given; ATGS is independent — `atgs_map` is built regardless of `no_odds`).
- [ ] **Step 4: Report source marker** — in `scorito/report.py`, in the topscorer table loop replace the row append with:
```python
    for c in result.topscorers:
        src = "📈" if c.get("goals_src") in ("market", "blend") else "✍️"
        L.append(f"| {c['name']} | {c['team']} | {c['position']} | "
                 f"{'✓' if c.get('pen_taker') else ''} | {src} | {c['ev']:.2f} |")
```
and update the table header two lines above from `"| Player | Team | Pos | Pen | EV |"` /
`"|---|---|---|---|---|"` to `"| Player | Team | Pos | Pen | Src | EV |"` /
`"|---|---|---|---|---|---|"`; and after the intro append:
```python
    n_mkt = sum(1 for c in result.topscorers if c.get("goals_src") in ("market", "blend"))
    if n_mkt:
        L.append(f"_📈 = anytime-goalscorer market rate ({n_mkt}/{len(result.topscorers)}); "
                 f"✍️ = hand-estimated g90._\n")
```
- [ ] **Step 5: Run** `.venv/bin/python -m pytest -q` → PASS (no-ATGS path unchanged).
- [ ] **Step 6: Commit** `git add scorito/main.py scorito/report.py && git commit -m "feat(atgs): --atgs/--atgs-file CLI + wiring + report source marker"`

## Task 5: real run, validation, aliases, README

**Files:** Modify `scorito/data/odds.py` (aliases), `README.md`; Create `docs/atgs-market-goal-rates-2026-06-09.md`

- [ ] **Step 1: Pull + cache ATGS (user runs — needs the key).** Have the user run:
  `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --odds-key "$ODDS_API_KEY" --atgs --risk balanced`
  This caches `data/cache/atgs_raw.json` (gitignored). Confirm it wrote and the run completed.
- [ ] **Step 2: Inspect coverage + add aliases** — from the cached feed, list how many of our candidates matched vs missed:
```bash
.venv/bin/python - <<'PY'
import json
from scorito.data import fixtures, odds
from scorito.data.topscorer_candidates import CANDIDATES
from scorito.main import _default_fixtures
matches = fixtures.load_fixtures(_default_fixtures())
amap = odds.parse_atgs(json.load(open("data/cache/atgs_raw.json")))
for c in CANDIDATES:
    cms = [(m.team1, m.team2) for m in matches if c["team"] in (m.team1, m.team2)]
    k = odds._norm(odds.ATGS_PLAYER_ALIASES.get(c["name"], c["name"]))
    hit = sum(1 for (h, a) in cms if (amap.get((h, a)) or amap.get((a, h)) or {}).get(k))
    print(f"{'OK ' if hit else 'MISS'} {hit}/{len(cms)}  {c['name']} ({c['team']})")
# Show some priced names per match to spot spelling mismatches for MISSes:
for key in list(amap)[:4]:
    print(key, sorted(amap[key])[:6])
PY
```
  For each MISS that is actually priced under a different spelling, add an entry to `ATGS_PLAYER_ALIASES`
  in `scorito/data/odds.py` (`{"Our Name": "Feed Name"}`), then re-run the inspection until coverage is
  maximized. Commit the aliases: `git add scorito/data/odds.py && git commit -m "feat(atgs): player-name aliases for feed spellings"`
- [ ] **Step 3: Validate** — re-run from cache and sanity-check:
  `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --atgs-file data/cache/atgs_raw.json --risk balanced`
  Confirm: the run completes; elite scorers show plausible market rates (Kane/Mbappé implied P(score)/match ~0.4-0.6 → `exp_goals` over 3 games ~1.5-2.5); the report shows 📈 markers; the recommended 6 are sensible. Note whether the blend changed the picks vs hand `g90`.
- [ ] **Step 4: Finding doc** — create `docs/atgs-market-goal-rates-2026-06-09.md`: coverage (N/total candidates market-priced), a few before/after `exp_goals` for elite + defender candidates, whether the recommended 6 changed, and the verdict (market sharper / no material change).
- [ ] **Step 5: README** — note topscorer goal rates can be sourced from live anytime-goalscorer odds via `--atgs`/`--atgs-file` (blended with hand `g90`), linking the finding.
- [ ] **Step 6: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 7: Commit** `git add README.md docs/atgs-market-goal-rates-2026-06-09.md && git commit -m "docs: ATGS market goal-rate finding + README"`

---

## Self-Review

- **Spec coverage:** client §3 → Task 2; name-match §4 → Task 2 (+aliases Task 5); blend §5 → Task 3; wire-through §6 → Task 3; CLI §7 → Task 4; report §8 → Task 4; config §9 → Task 1; error handling §10 → Task 2 (skip failed events) + Task 3 (price>1 guard, clamp); testing §11 → Tasks 1-4; validation §12 → Task 5. Covered.
- **Placeholder scan:** none — complete code; `fetch_atgs` is network so it's validated in the real run (Task 5), with `parse_atgs`/`_norm`/`build_expected_goals` unit-tested.
- **Type consistency:** `parse_atgs -> {(home,away): {norm_name: price}}` consumed order-agnostically by `build_expected_goals`; `_norm`/`ATGS_PLAYER_ALIASES` defined in `odds.py` (Task 2) and imported in `topscorers.py` (Task 3); `exp_goals`/`goals_src` set by `build_expected_goals` and read by `score_candidate`/`fame_score`/`sample_player_goals` (Task 3) and `report.py` (Task 4); `run(..., atgs, atgs_file)` matches the `main()` call (Task 4).
- **Backward-compat:** `build_expected_goals` only runs when `atgs_map` is non-empty; all three consumers branch on `"exp_goals" in c`, so a no-ATGS run is byte-identical to today (asserted in Task 3 test).
- **Open risk:** the exact outcome field (`name` vs `description`) and player spellings are confirmed against the cached feed in Task 5; the parser handles both and aliases close the gaps.
