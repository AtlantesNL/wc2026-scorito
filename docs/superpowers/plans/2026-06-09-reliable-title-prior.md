# Reliable champion title prior (live market consensus) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Replace the hand-typed champion title prior with a live, de-vigged, multi-bookmaker WC-winner outright consensus from The Odds API (Opta kept as cross-check, MC as backbone), broadening market coverage so MC longshot inflation deflates.

**Architecture:** New `odds.fetch_winner_outrights`/`parse_winner_market` (proportional de-vig per book → median consensus); `priors.blended_probs(market=...)` consumes it; `main` fetches/replays it (`--winner-file`) and feeds both `blended_probs` call sites. Falls back to the hand-typed prior when absent.

**Tech Stack:** Python 3.12, requests, pytest. No new deps.

---

## Task 1: outright fetch + de-vig parser (`odds.py`)

**Files:** Modify `scorito/data/odds.py`, `tests/test_odds.py`

- [ ] **Step 1: Failing test** — append to `tests/test_odds.py`:
```python
def test_parse_winner_market_devigs_and_consensus():
    from scorito.data.odds import parse_winner_market
    raw = [{"bookmakers": [
        {"key": "b1", "markets": [{"key": "outrights", "outcomes": [
            {"name": "Spain", "price": 6.0}, {"name": "France", "price": 6.0},
            {"name": "Brazil", "price": 11.0}, {"name": "United States", "price": 81.0},
            {"name": "Argentina", "price": 13.0}, {"name": "England", "price": 9.0},
            {"name": "Germany", "price": 21.0}, {"name": "Netherlands", "price": 26.0}]}]},
        {"key": "b2", "markets": [{"key": "outrights", "outcomes": [
            {"name": "Spain", "price": 6.5}, {"name": "France", "price": 5.5},
            {"name": "Brazil", "price": 10.0}, {"name": "United States", "price": 71.0},
            {"name": "Argentina", "price": 12.0}, {"name": "England", "price": 9.5},
            {"name": "Germany", "price": 19.0}, {"name": "Netherlands", "price": 29.0}]}]},
    ]}]
    m = parse_winner_market(raw)
    assert abs(sum(m.values()) - 1.0) < 1e-9          # de-vigged consensus sums to 1
    assert m["USA"] == min(m.values())                 # "United States" -> USA, the longest shot
    assert max(m, key=m.get) in ("Spain", "France")    # favourites on top
    assert m["Spain"] > m["Brazil"] > m["USA"]         # de-vig preserves ordering
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_odds.py::test_parse_winner_market_devigs_and_consensus -q` → FAIL (no `parse_winner_market`).
- [ ] **Step 3: Implement** — append to `scorito/data/odds.py` (`statistics`, `requests`, `config` already imported):
```python
WINNER_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup_winner/odds"


def fetch_winner_outrights(api_key, regions=None):
    """Live WC-winner outright (futures) odds across books. Returns the raw JSON (cache it; replay
    via --winner-file). One request x regions (~2 credits)."""
    r = requests.get(WINNER_URL, params=dict(regions=regions or config.ATGS_REGIONS,
                     markets="outrights", oddsFormat="decimal", apiKey=api_key), timeout=30)
    r.raise_for_status()
    return r.json()


def parse_winner_market(raw):
    """``raw``: outright /odds response. -> ``{team_ofb: consensus_prob}`` (de-vigged, sums to 1).
    Proportional de-vig per book (robust to the long tail of unlisted minnows), median across books."""
    per_book = []
    for ev in raw:
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk.get("key") != "outrights":
                    continue
                prices = {_ofb(o["name"]): o["price"] for o in mk.get("outcomes", [])
                          if o.get("price", 0) > 1.0}
                if len(prices) < 8:           # too thin to de-vig reliably
                    continue
                inv = {t: 1.0 / p for t, p in prices.items()}
                s = sum(inv.values()) or 1.0
                per_book.append({t: v / s for t, v in inv.items()})   # proportional de-vig -> sum 1
    if not per_book:
        return {}
    teams = set().union(*per_book)
    cons = {t: statistics.median([b[t] for b in per_book if t in b]) for t in teams}
    tot = sum(cons.values()) or 1.0
    return {t: p / tot for t, p in cons.items()}   # renormalize the median consensus to sum 1
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_odds.py -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/data/odds.py tests/test_odds.py && git commit -m "feat(title): The Odds API WC-winner outright fetch + de-vigged consensus parser"`

## Task 2: `blended_probs(market=...)` (`priors.py`)

**Files:** Modify `scorito/data/priors.py`, `tests/test_priors.py`

- [ ] **Step 1: Failing test** — append to `tests/test_priors.py`:
```python
def test_blended_probs_uses_live_market_and_includes_market_only_teams():
    from scorito.data.priors import blended_probs, OPTA
    live = {"Spain": 0.16, "Morocco": 0.03}        # Spain is in Opta; Morocco is market-only
    b = blended_probs(market=live)
    assert b["Spain"] == pytest.approx(0.5 * OPTA["Spain"] + 0.5 * 0.16)
    assert b["Morocco"] == pytest.approx(0.03)      # market-only team included at its market prob
    assert b["Argentina"] == OPTA["Argentina"]      # not in the live market -> Opta only
    assert blended_probs()["England"] == pytest.approx(0.5 * OPTA["England"] + 0.5 * 0.11)  # no-arg fallback unchanged
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_priors.py::test_blended_probs_uses_live_market_and_includes_market_only_teams -q` → FAIL (`blended_probs` takes no arg).
- [ ] **Step 3: Implement** — in `scorito/data/priors.py` replace `blended_probs` with:
```python
def blended_probs(market: dict | None = None) -> dict[str, float]:
    """Genuine title probabilities: average Opta + market (the live de-vigged consensus when given,
    else the hand-typed MARKET fallback). Market-only teams (in the consensus but not Opta) are
    included at their market prob, so ~30 teams get a real anchor instead of the MC's estimate."""
    mkt = market if market else MARKET
    out = {}
    for team, p in OPTA.items():
        out[team] = 0.5 * p + 0.5 * mkt[team] if team in mkt else p
    for team, mp in mkt.items():
        if team not in out:
            out[team] = mp
    return out
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_priors.py -q` → PASS (existing tests + new).
- [ ] **Step 5: Commit** `git add scorito/data/priors.py tests/test_priors.py && git commit -m "feat(title): blended_probs accepts a live market consensus (+ market-only teams)"`

## Task 3: wire into `main.py` + CLI

**Files:** Modify `scorito/main.py`

- [ ] **Step 1: `run` signature** — add `winner_file=None` after `atgs_file=None,` in the `run(...)` signature.
- [ ] **Step 2: Fetch/parse the winner map** — in `scorito/main.py`, immediately after the `atgs_map = odds_mod.parse_atgs(atgs_raw)` line (end of the ATGS block) insert:
```python
    winner_map = {}
    if winner_file or (not no_odds and odds_key):
        from scorito.data import odds as odds_mod
        if winner_file:
            winner_raw = json.load(open(winner_file, encoding="utf-8"))
        else:
            winner_raw = odds_mod.fetch_winner_outrights(odds_key)
            os.makedirs("data/cache", exist_ok=True)
            with open("data/cache/winner_raw.json", "w", encoding="utf-8") as f:
                json.dump(winner_raw, f)
        winner_map = odds_mod.parse_winner_market(winner_raw)
```
- [ ] **Step 3: Feed both `blended_probs` sites** — change `pwin = blend_champion_probs(sim["win"], blended_probs())` to:
```python
        pwin = blend_champion_probs(sim["win"], blended_probs(market=winner_map or None))
```
and change the fallback `pwin = blended_probs()` to:
```python
        pwin = blended_probs(market=winner_map or None)
```
- [ ] **Step 4: argparse + call** — after the `--atgs-file` argument add:
```python
    p.add_argument("--winner-file", default=None, help="load a saved WC-winner outright JSON instead of fetching")
```
and add `winner_file=args.winner_file,` to the `run(...)` call (next to `atgs_file=args.atgs_file`).
- [ ] **Step 5: Run** `.venv/bin/python -m pytest -q` → PASS (no-winner path: `winner_map={}` → `None` → hand-typed fallback, unchanged).
- [ ] **Step 6: Commit** `git add scorito/main.py && git commit -m "feat(title): --winner-file/auto-fetch + feed live consensus into the champion prior"`

## Task 4: verify live, validate, README

**Files:** Create `docs/reliable-title-prior-2026-06-09.md`; Modify `README.md`; verification

- [ ] **Step 1: Verify the outright is live + cache it (user runs — needs the key):**
  `.venv/bin/python -c "import json,os; from scorito.data import odds; raw=odds.fetch_winner_outrights(os.environ['ODDS_API_KEY']); json.dump(raw, open('data/cache/winner_raw.json','w')); m=odds.parse_winner_market(raw); print(len(m),'teams; top:', sorted(m.items(), key=lambda kv:-kv[1])[:6])"`
  Expected: a non-empty consensus (e.g. `28 teams; top: [('Spain',0.16),('France',0.16),...]`). If it prints `0 teams`, the outright isn't live on the free tier yet — the model falls back to the hand-typed prior (no regression); note it and skip to Step 4 documenting that.
- [ ] **Step 2: Cross-check consensus vs Opta vs Polymarket** — run:
```bash
.venv/bin/python - <<'PY'
import json
from scorito.data import odds
from scorito.data.priors import OPTA
m = odds.parse_winner_market(json.load(open("data/cache/winner_raw.json")))
poly = {"France":.16,"Spain":.16,"England":.11,"Portugal":.10,"Argentina":.08,"Brazil":.08,"Germany":.05,"Netherlands":.04}
print(f"{'Team':13}{'consensus':>10}{'Opta':>7}{'Polymkt':>8}")
for t in sorted(m, key=lambda t: -m[t])[:12]:
    print(f"{t:13}{m[t]*100:>9.1f}%{(f'{OPTA[t]*100:.1f}%' if t in OPTA else '-'):>7}{(f'{poly[t]*100:.0f}%' if t in poly else '-'):>8}")
PY
```
  Expected: the consensus broadly agrees with Polymarket/Opta (Spain/France ~15-17%, England/Portugal ~9-11%); flag any wild divergence (parse/name-mapping issue — add `_ofb`/`ODDS_TO_OPENFOOTBALL` mappings for any garbled team names and re-run).
- [ ] **Step 3: Real run + champion sanity** — `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --atgs-file data/cache/atgs_raw.json --winner-file data/cache/winner_raw.json --risk balanced`, then:
```bash
.venv/bin/python - <<'PY'
from scorito.main import run
res = run(no_odds=False, pool_size=32, risk="balanced", odds_file="data/cache/odds_raw.json",
          atgs_file="data/cache/atgs_raw.json", winner_file="data/cache/winner_raw.json")
print(f"{'Team':12}{'outright':>9}{'Win-pool':>10}")
for r in res.champion[:8]:
    wp = res.pool_win.get(r.team)
    print(f"{r.team:12}{r.p_win*100:>8.1f}%{(f'{wp*100:.1f}%' if wp is not None else '-'):>10}")
print("recommended:", res.champion[0].team)
PY
```
  Expected: the title outrights are now market-grounded; previously-inflated longshots (Colombia/Ecuador) sit at their real low level; recommendation sensible (likely Spain). **If the MC still inflates non-market teams into the top Win-pool**, raise `config.CHAMPION_MARKET_WEIGHT` to 0.65, re-run, and note it in the doc.
- [ ] **Step 4: Finding doc** — create `docs/reliable-title-prior-2026-06-09.md`: the consensus-vs-Opta-vs-Polymarket table, coverage (N teams), the before/after on longshot inflation, whether `CHAMPION_MARKET_WEIGHT` was raised, and the champion result.
- [ ] **Step 5: README** — note the champion prior can be sourced from a live de-vigged multi-bookmaker outright via `--winner-file`/auto-fetch (Opta cross-check, hand-typed fallback), linking the finding.
- [ ] **Step 6: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 7: Commit** `git add docs/reliable-title-prior-2026-06-09.md README.md && git commit -m "docs: live title-prior finding + README"`

---

## Self-Review
- **Spec coverage:** fetch/de-vig §3 → Task 1; combination §4 → Task 2; wiring §5 → Task 3; validation §6 → Task 4; fallback §7 → Task 3 (`winner_map or None`); config §8 → Task 4 (conditional weight); testing §9 → Tasks 1-3. Covered.
- **Placeholder scan:** none — complete code + runnable diagnostics; `fetch_winner_outrights` is network so validated in the real run (Task 4), with `parse_winner_market`/`blended_probs` unit-tested.
- **Type consistency:** `parse_winner_market -> {team: prob}` consumed by `blended_probs(market=...)` (Task 2) and passed from `main` as `winner_map` (Task 3); `fetch_winner_outrights(api_key, regions)` matches its caller; `_ofb` reused for name mapping.
- **Backward-compat:** `blended_probs()` default `market=None` → hand-typed `MARKET` (Task 2 test asserts unchanged); `winner_map or None` means no feed → today's behavior. Zero regression.
- **Risk:** the outright may not be live 2 days out (Task 4 Step 1 verifies; fallback covers it); team-name mismatches surface in Step 2 and are mapped via `ODDS_TO_OPENFOOTBALL`.
