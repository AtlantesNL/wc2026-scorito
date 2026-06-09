# Champion robustness recalibration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the champion recommendation robust at a realistic amateur field (default → Spain, Argentina shown as a leverage dart) by lowering FIELD_SHARPNESS, sweeping realistic dispersions, adding real market anchors, and fixing the report's SE label.

**Architecture:** Four small calibration edits (config sharpness, pool sweep default, priors market dict, report text) + a real-run validation. No logic restructuring; the "goal realism" half was verified unnecessary and dropped.

**Tech Stack:** Python 3.12, numpy, pytest.

---

## Task 1: realistic FIELD_SHARPNESS

**Files:** Modify `scorito/config.py`, `tests/test_config.py`

- [ ] **Step 1: Failing test** — append to `tests/test_config.py`:
```python
def test_field_sharpness_realistic():
    assert 1.0 <= config.FIELD_SHARPNESS <= 2.0   # amateur dispersion, not syndicate-chalk
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_config.py::test_field_sharpness_realistic -q` → PASS at 2.0 currently (boundary). To make it a real guard, **first** assert `< 2.0`:
  temporarily use `assert 1.0 <= config.FIELD_SHARPNESS < 2.0` → run → FAIL at 2.0. (Then keep `<= 2.0` after the change; the `< 2.0` proves the test bites.)
- [ ] **Step 3: Implement** — in `scorito/config.py` change the `FIELD_SHARPNESS` line to:
```python
FIELD_SHARPNESS = 1.5      # field chalkiness exponent (1 = rivals pick ~ true prob; higher = chalkier).
                           # 1.5 = realistic amateur dispersion (chase news-favourites somewhat, disperse
                           # on feelings/home bias) — NOT a syndicate field (2.0+ over-leverages longshots).
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_config.py -q` → PASS (revert the test to `<= 2.0`).
- [ ] **Step 5: Commit** `git add scorito/config.py tests/test_config.py && git commit -m "feat(champion): FIELD_SHARPNESS 2.0 -> 1.5 (realistic amateur field)"`

## Task 2: real market anchors in priors

**Files:** Modify `scorito/data/priors.py`, `tests/test_priors.py`

- [ ] **Step 1: Failing test** — append to `tests/test_priors.py`:
```python
def test_market_anchors_include_argentina_and_lower_its_prior():
    from scorito.data.priors import MARKET, OPTA, blended_probs
    assert {"Spain", "France", "England", "Argentina", "Brazil"} <= set(MARKET)
    b = blended_probs()
    assert b["Argentina"] < OPTA["Argentina"]      # the ~8% market anchor pulls Argentina down
    assert b["Germany"] == OPTA["Germany"]         # uncovered team still uses Opta unchanged
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_priors.py::test_market_anchors_include_argentina_and_lower_its_prior -q` → FAIL (Argentina not in MARKET).
- [ ] **Step 3: Implement** — in `scorito/data/priors.py` replace the `MARKET` dict with (Polymarket, June 2026):
```python
# Prediction-market title probabilities (Polymarket, ~June 2026). Spain/France co-favourites; Argentina
# and Brazil trail the European favourites. Averaged with Opta in blended_probs (NOT renormalized).
MARKET = {
    "Spain": 0.16,
    "France": 0.16,
    "England": 0.11,
    "Argentina": 0.08,
    "Brazil": 0.08,
}
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_priors.py -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/data/priors.py tests/test_priors.py && git commit -m "feat(champion): real Polymarket title anchors (de-inflate Argentina outright)"`

## Task 3: realistic stability sweep

**Files:** Modify `scorito/model/pool.py`, `tests/test_pool.py`

- [ ] **Step 1: Failing test** — append to `tests/test_pool.py`:
```python
def test_pool_win_champion_default_sharpnesses_are_realistic():
    import inspect
    sweep = inspect.signature(pool.pool_win_champion).parameters["sharpnesses"].default
    assert all(s <= 2.0 for s in sweep) and min(sweep) <= 1.0   # plausible amateur dispersions only
```
- [ ] **Step 2: Run** `.venv/bin/python -m pytest tests/test_pool.py::test_pool_win_champion_default_sharpnesses_are_realistic -q` → FAIL (default is `(1.5, 2.0, 3.0)`; 3.0 > 2.0).
- [ ] **Step 3: Implement** — in `scorito/model/pool.py` change the `pool_win_champion` signature line
  `sims=config.POOL_WIN_SIMS, sharpnesses=(1.5, 2.0, 3.0)):` to:
```python
                      sims=config.POOL_WIN_SIMS, sharpnesses=(1.0, 1.5, 2.0)):
```
- [ ] **Step 4: Run** `.venv/bin/python -m pytest tests/test_pool.py -q` → PASS.
- [ ] **Step 5: Commit** `git add scorito/model/pool.py tests/test_pool.py && git commit -m "feat(champion): sweep realistic dispersions (1.0,1.5,2.0) not chalk extremes"`

## Task 4: report — SE label + robust/dart framing

**Files:** Modify `scorito/report.py`

- [ ] **Step 1: Implement** — in `scorito/report.py` replace the champion recommendation block (the
  `rec = result.champion[0]` block through the `else:`/`runner` lines) with:
```python
    rec = result.champion[0]
    wp = result.pool_win.get(rec.team)
    if wp is not None:
        sims = result.meta.get("pool_win_sims", 0) or 1
        top = max(result.pool_win.values())
        se = (max(top * (1.0 - top), 1e-9) / sims) ** 0.5          # Monte-Carlo std error
        cluster = sorted((t for t, p in result.pool_win.items() if p >= top - 2 * se),
                         key=lambda t: -result.pool_win[t])
        names = ", ".join(f"{t} {result.pool_win[t]:.1%}" for t in cluster[:5])
        dart = max(result.champion, key=lambda r: r.leverage)
        dart_txt = ("" if dart.team == rec.team else
                    f" If your pool is unusually chalk-heavy on the favourites, **{dart.team}** is the "
                    f"higher-leverage differentiation dart.")
        L.append(f"\n**Champion — robust pick: {rec.team}** ({wp:.1%} pool-win, the highest floor at a "
                 f"realistic field; within ~2 Monte-Carlo std-errors ±{2 * se:.1%} of the cluster "
                 f"[{names}]).{dart_txt} Avoid host nations (USA/Mexico/Canada), which amateurs "
                 f"over-pick.\n")
    else:
        runner = result.champion[1]
        L.append(f"\n**Recommendation: {rec.team}** (pool-adjusted leverage); "
                 f"{runner.team} close.\n")
```
  (Changes: `±{2 * se:.1%}` now matches the "~2 std-errors" wording and the `top − 2·se` cluster; the
  recommendation leads with the robust pool-win pick `rec` and names the max-leverage `dart` separately.)
- [ ] **Step 2: Run** `.venv/bin/python -m pytest -q` → PASS (no test asserts the exact wording; nothing breaks).
- [ ] **Step 3: Commit** `git add scorito/report.py && git commit -m "fix(report): correct champion SE label (2-sigma) + robust-pick/dart framing"`

## Task 5: validation + finding doc

**Files:** Create `docs/champion-robustness-2026-06-09.md`; verification

- [ ] **Step 1: Real run** — `.venv/bin/python -m scorito.main --odds-file data/cache/odds_raw.json --atgs-file data/cache/atgs_raw.json --risk balanced`. Expected: champion default is now **Spain** (robust), report shows the dart (Argentina/Portugal) + corrected ±SE; capture the champion table.
- [ ] **Step 2: Champion before/after + topscorer re-validation** — run this diagnostic (champion table at the new sharpness, and confirm the topscorer engine still beats its EV+reserve baseline at FIELD_SHARPNESS=1.5):
```bash
.venv/bin/python - <<'PY'
from scorito.main import run
from scorito import config
res = run(no_odds=False, pool_size=32, risk="balanced",
          odds_file="data/cache/odds_raw.json", atgs_file="data/cache/atgs_raw.json")
print("FIELD_SHARPNESS =", config.FIELD_SHARPNESS)
print(f"{'Team':12}{'outright':>9}{'ownership':>10}{'Win-pool':>10}{'lev':>8}")
for r in res.champion[:8]:
    wp = res.pool_win.get(r.team)
    print(f"{r.team:12}{r.p_win*100:>8.1f}%{r.est_share*100:>9.0f}%{(f'{wp*100:.1f}%' if wp is not None else '-'):>10}{r.leverage:>8.4f}")
print("recommended:", res.champion[0].team, "| topscorers:", [c['name'] for c in res.topscorers])
print("ts entry pool-win:", res.meta.get("ts_pool_win"))
PY
```
  Expected: `recommended: Spain`; the engine topscorers still selected with a sensible `ts_pool_win` (the safeguard guarantees ≥ baseline). If `recommended` is NOT Spain, note which team and at what Win-pool, and report back before finalizing.
- [ ] **Step 3: Finding doc** — create `docs/champion-robustness-2026-06-09.md`: the before (sharpness 2.0 → Argentina) vs after (1.5 → Spain) champion tables, the realistic-field rationale, the market-anchor change, and the topscorer re-validation result.
- [ ] **Step 4: Final suite** `.venv/bin/python -m pytest -q` → all pass.
- [ ] **Step 5: Commit** `git add docs/champion-robustness-2026-06-09.md && git commit -m "docs: champion-robustness finding (Spain robust default; Argentina the dart)"`

---

## Self-Review

- **Spec coverage:** §3 sharpness → Task 1; §5 market → Task 2; §4 sweep → Task 3; §6 report → Task 4; §7 validation → Task 5; §9 tests → Tasks 1-3. Covered.
- **Placeholder scan:** none — complete code + runnable diagnostic.
- **Type consistency:** Task 4 uses existing `ChampionRec` fields (`team`, `leverage`) and `result.pool_win`/`meta` already populated by `main`; the sweep default tuple in Task 3 matches the test in Task 3; `MARKET` keys in Task 2 all exist in `OPTA` (required by `blended_probs`).
- **Risk:** `FIELD_SHARPNESS` is global, so Task 5 re-validates the topscorer engine (safeguarded ≥ baseline) and that the champion flips to Spain; if the champion does NOT become Spain, Step 2 says to report back rather than silently finalize.
