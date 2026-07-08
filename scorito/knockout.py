"""Knockout-phase pick engine (Round of 32 and onward).

Reuses the group-phase goal engine (market odds -> Dixon-Coles grid) but with knockout scoring:
match XOR exact/toto on the "stand na 120 min" result and single-game topscorers, both per-round via
``config.KO_ROUND_SCORING`` (R32 90/60 · 16/32/64; R16 135/90 · 24/48/96). Protect-the-lead posture:
scorelines are pure EV; topscorer *ranking* additionally shrinks the multiplier toward the attacker's
(``lead_shrink``) so the slate mirrors the chalk field instead of chasing under-owned differentials.

Pure helpers (``blend_g90``, ``et_adjusted_grid``, ``filter_alive``, ``best_scoreline``) are unit
tested; ``run_knockout`` wires them through the existing odds/Elo/grid/topscorer code.
"""
from scorito import config
from scorito.model.grid import build_grid
from scorito.model.match_ev import score_ev


def blend_g90(club_g90, tourn_nonpen_goals, games, prior_games=config.FORM_PRIOR_GAMES):
    """Effective non-penalty g90 = the tournament rate shrunk toward the club prior.

    ``(prior_games*club_g90 + tourn_nonpen_goals) / (prior_games + games)``. With games=0 this is just
    the club rate. Lifts in-form scorers (Messi) and fades goal-shy creators (Wirtz) — the group-stage
    retrospective showed club-g90 alone was the topscorer model's one real weakness. Tournament goals
    are NON-PENALTY (pens stay in the separate pen_share term, so no double-count)."""
    return (prior_games * club_g90 + tourn_nonpen_goals) / (prior_games + games)


def et_adjusted_grid(lam_home, lam_away, et_share=config.ET_MINUTE_SHARE):
    """Dixon-Coles grid for the recorded 120' score. A match level after 90' plays ~30 more minutes,
    so scale both lambdas by (1 + et_share * P(draw@90')) — modest uplift, more goals, fewer draws."""
    g90 = build_grid(lam_home, lam_away)
    bump = 1.0 + et_share * g90.p_draw
    return build_grid(lam_home * bump, lam_away * bump)


def best_scoreline(grid, pts_exact=config.PTS_KO_EXACT, pts_toto=config.PTS_KO_TOTO):
    """The (i, j) maximising knockout EV = (exact-toto)*P(i-j) + toto*P(toto). Returns
    ``(home, away, ev)``. Pure EV (no leverage) — the max_ev / protect-the-lead pick."""
    n = grid.matrix.shape[0]
    best, best_ev = (1, 0), -1.0
    for i in range(n):
        for j in range(n):
            ev = score_ev(grid, i, j, pts_exact=pts_exact, pts_toto=pts_toto)
            if ev > best_ev:
                best, best_ev = (i, j), ev
    return best[0], best[1], best_ev


def filter_alive(candidates, alive_teams, injured_out=frozenset()):
    """Keep candidates whose team is still in the tournament and who are not injured-out this round."""
    return [c for c in candidates
            if c["team"] in alive_teams and c["name"] not in injured_out]


# --------------------------------------------------------------------------------------------------
# Orchestration: wire the helpers through the existing odds/Elo/grid/topscorer code for a round.
# --------------------------------------------------------------------------------------------------
import datetime
import json
import os
import warnings
from collections import defaultdict

from scorito.data import elo as elo_mod
from scorito.data.knockout_fixtures import (ALIVE_TEAMS, INJURED_OUT, R32_START_OVERRIDES,
                                            R32_TIES, TIE_NOTES)
from scorito.data.odds import _norm
from scorito.data.topscorer_candidates import CANDIDATES
from scorito.model.goals import expected_goals
from scorito.model.topscorers import build_expected_goals, score_candidate, shrink_mult


def load_results_nonpen_goals(path):
    """``{normalized_name: non-penalty group-stage goals}`` from an openfootball results file.
    Penalties (and own goals) are excluded so the realized-form blend doesn't double-count the
    separate pen_share term. Missing/unreadable file -> empty (blend then leaves g90 == club rate)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    tally = {}
    for m in data.get("matches", []):
        for side in ("goals1", "goals2"):
            for g in (m.get(side) or []):
                if g.get("owngoal") or g.get("penalty"):
                    continue
                key = _norm(g.get("name", ""))
                if key:
                    tally[key] = tally.get(key, 0) + 1
    return tally


def _round_tag(round_name):
    """Short round tag ("r32"/"r16"/"qf") used for cache filenames and the default out dir —
    kept identical to the CLI --round choices so paths match what the runbooks reference."""
    return round_name.lower().replace("round of ", "r").replace("quarterfinal", "qf").replace(" ", "")


def _load_odds(odds_key, odds_file, cache_tag="r32"):
    if not (odds_key or odds_file):
        return None
    from scorito.data import odds as odds_mod
    if odds_file:
        raw = json.load(open(odds_file, encoding="utf-8"))
    else:
        raw = odds_mod.fetch_odds(odds_key)
        os.makedirs("data/cache", exist_ok=True)
        with open(f"data/cache/odds_{cache_tag}_raw.json", "w", encoding="utf-8") as f:
            json.dump(raw, f)
    return odds_mod.parse_odds(raw)


def _load_atgs(odds_key, atgs_file, atgs, cache_tag="r32"):
    if not (atgs_file or (atgs and odds_key)):
        return {}
    from scorito.data import odds as odds_mod
    if atgs_file:
        raw = json.load(open(atgs_file, encoding="utf-8"))
    else:
        raw = odds_mod.fetch_atgs(odds_key)
        os.makedirs("data/cache", exist_ok=True)
        with open(f"data/cache/atgs_{cache_tag}_raw.json", "w", encoding="utf-8") as f:
            json.dump(raw, f)
    return odds_mod.parse_atgs(raw)


def lead_dashboard(standings, scoring):
    """Markdown lead-protection readout: gap to each rival + how many R16 swing events erase it.

    A leader minimises variance vs the field; this quantifies how safe the cushion is in the round's
    own point units. Swing units: an exact instead of a toto = ``exact-toto``; a differential
    topscorer goal = that position's multiplier."""
    you = standings["you"]
    exact_swing = scoring["exact"] - scoring["toto"]
    m = scoring["mult"]
    L = ["\n## Lead-protection dashboard\n",
         f"_Standings {standings.get('as_of', '')}._ You: **{you}**.\n",
         "| Rival | Points | Your lead | Exacts to erase it | Their live differential |",
         "|---|---|---|---|---|"]
    for r in standings["rivals"]:
        gap = you - r["points"]
        exacts = gap / exact_swing if exact_swing else float("inf")
        L.append(f"| {r['name']} | {r['points']} | **+{gap}** | ~{exacts:.1f} "
                 f"(×{exact_swing} each) | {r.get('diff_topscorer', '—')} |")
    L.append(f"\n_R16 swing units — exact vs toto **+{exact_swing}**, ATT goal **+{m['ATT']}**, "
             f"MID goal **+{m['MID']}**, DEF/GK goal **+{m['DEF']}**. Both rivals play pure chalk and "
             "mirror our slate, so realised variance is low: mirror the chalk, hand them no topscorer "
             "differential, take no contrarian picks._\n")
    return "\n".join(L)


def run_knockout(ties=R32_TIES, odds_key=None, odds_file=None, atgs=False, atgs_file=None,
                 results_file="data/cache/worldcup2026_results.json", out_dir=None,
                 round_name="Round of 32", *, alive_teams=None, injured_out=None,
                 start_overrides=None, tie_notes=None, standings=None):
    """Generate max_ev knockout picks: per-tie scoreline + advancer, and single-game topscorers.

    Round-aware via ``config.KO_ROUND_SCORING[round_name]`` (points, multipliers, form-games, brace
    de-bias). The fixtures bundle (``ties``/``alive_teams``/``injured_out``/``start_overrides``/
    ``tie_notes``) and ``standings`` default to the R32 module data, so an argument-free call
    reproduces the shipped R32 run exactly; pass the R16 bundle for the Round of 16."""
    scoring = config.KO_ROUND_SCORING[round_name]
    alive_teams = ALIVE_TEAMS if alive_teams is None else alive_teams
    injured_out = INJURED_OUT if injured_out is None else injured_out
    start_overrides = R32_START_OVERRIDES if start_overrides is None else start_overrides
    tie_notes = TIE_NOTES if tie_notes is None else tie_notes
    cache_tag = _round_tag(round_name)  # -> "r32" / "r16" / "qf"
    out_dir = out_dir or f"out/ko_{cache_tag}"

    teams = sorted({t for m in ties for t in (m.team1, m.team2)})
    elo_map = elo_mod.get_elo(teams)
    odds_map = _load_odds(odds_key, odds_file, cache_tag)
    atgs_map = _load_atgs(odds_key, atgs_file, atgs, cache_tag)

    # Per-tie: market (or Elo) expected goals -> ET-adjusted 120' grid -> EV-max scoreline + advancer.
    match_picks, match_lams_et, team_lam = [], {}, defaultdict(list)
    priced = 0
    for m in ties:
        l1, l2 = expected_goals(m, odds_map, elo_map)
        if odds_map and ((m.team1, m.team2) in odds_map or (m.team2, m.team1) in odds_map):
            priced += 1
        grid90 = build_grid(l1, l2)
        bump = 1.0 + config.ET_MINUTE_SHARE * grid90.p_draw
        e1, e2 = l1 * bump, l2 * bump
        grid = build_grid(e1, e2)
        h, a, ev = best_scoreline(grid, pts_exact=scoring["exact"], pts_toto=scoring["toto"])
        adv = m.team1 if grid.p_home >= grid.p_away else m.team2
        match_picks.append(dict(tie=m, home=h, away=a, ev=ev, p_home=grid.p_home,
                                p_draw=grid.p_draw, p_away=grid.p_away, adv=adv))
        match_lams_et[(m.team1, m.team2)] = (e1, e2)
        team_lam[m.team1].append(e1)
        team_lam[m.team2].append(e2)

    means = {t: sum(v) / len(v) for t, v in team_lam.items()}
    avg = sum(means.values()) / len(means)
    team_factors = {t: means[t] / avg for t in means}

    # Topscorers: alive+fit candidates, per-round start overrides + realized-form g90 blend (form-games
    # entering the round), single-game opponent-specific expected goals, round multipliers with the
    # brace de-bias, pure EV (max_ev) top-N.
    nonpen = load_results_nonpen_goals(results_file)
    adjusted = []
    for c in filter_alive(CANDIDATES, alive_teams, injured_out):
        tg = nonpen.get(_norm(c["name"]), 0)
        adjusted.append(dict(c, start_prob=start_overrides.get(c["name"], c["start_prob"]),
                             g90=blend_g90(c["g90"], tg, games=scoring["form_games"]), tourn_goals=tg))
    kept = build_expected_goals(adjusted, ties, atgs_map, team_factors,
                                match_lams=match_lams_et, avg_lam=avg, pen_bonus=scoring["pen_bonus"])
    # ko_ev = true expected points (for display + the dashboard). ko_sel = the lead-protection ranking
    # score: the same de-biased EV but with the multiplier compressed toward the attacker's, so we
    # mirror the chalk field and don't rank an under-owned DEF/MID differential into the slate.
    sel_mult = shrink_mult(scoring["mult"], scoring.get("lead_shrink", 1.0))
    for c in kept:
        c["ko_ev"] = score_candidate(c, team_factors, mult=scoring["mult"],
                                     brace_credit=scoring["brace_credit"])
        c["ko_sel"] = score_candidate(c, team_factors, mult=sel_mult,
                                      brace_credit=scoring["brace_credit"])
    ranked = sorted(kept, key=lambda c: c["ko_sel"], reverse=True)
    slots = scoring["slots"]
    top4 = ranked[:slots]

    # Match-diversified variant: at most one pick per tie (cuts correlation for a lead-protector).
    opp_tie = {t: (m.team1, m.team2) for m in ties for t in (m.team1, m.team2)}
    diversified, used_ties = [], set()
    for c in ranked:
        key = opp_tie[c["team"]]
        if key in used_ties:
            continue
        diversified.append(c)
        used_ties.add(key)
        if len(diversified) >= slots:
            break

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    result = dict(round_name=round_name, match_picks=match_picks, top4=top4,
                  diversified=diversified, ranked=ranked, odds_coverage=(priced, len(ties)),
                  used_odds=bool(odds_map), used_atgs=bool(atgs_map), generated_at=generated_at,
                  scoring=scoring, tie_notes=tie_notes, standings=standings)
    _write_ko_report(result, out_dir)
    return result


def _opp_label(team, match_picks):
    for p in match_picks:
        m = p["tie"]
        if team == m.team1:
            return m.team2
        if team == m.team2:
            return m.team1
    return "?"


def _ts_row(c, match_picks):
    src = {"market": "📈", "hand": "✍️", "blend": "📊"}.get(c.get("goals_src"), "✍️")
    return (f"| {c['name']} | {c['team']} | {c['position']} | {_opp_label(c['team'], match_picks)} "
            f"| {c.get('tourn_goals', 0)} | {src} | {round(c['ko_ev'], 1)} |")


def _write_ko_report(r, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mp = r["match_picks"]
    sc = r["scoring"]
    mlt = sc["mult"]
    tie_notes = r.get("tie_notes") or {}
    goal_model = "market odds + Elo" if r["used_odds"] else "Elo only"
    atgs_note = " + ATGS" if r["used_atgs"] else ""
    total_ev = sum(p["ev"] for p in mp) + sum(c["ko_ev"] for c in r["top4"])
    L = []
    L.append(f"# Scorito WC2026 — {r['round_name']} picks (max_ev / protect-the-lead)\n")
    L.append(f"_Goal model:_ {goal_model}{atgs_note} · _Odds-priced:_ {r['odds_coverage'][0]}/"
             f"{r['odds_coverage'][1]} · _Generated:_ {r['generated_at']}\n")
    L.append(f"_Scoring:_ exact **{sc['exact']}** / toto **{sc['toto']}** (XOR, result after 120'); "
             f"topscorers ATT {mlt['ATT']} / MID {mlt['MID']} / DEF·GK {mlt['DEF']}, goals this round only.\n")
    L.append(f"\n**Model expected points ({len(mp)} ties + {len(r['top4'])} topscorers):** "
             f"{total_ev:.0f}\n")
    if r.get("standings"):
        L.append(lead_dashboard(r["standings"], sc))
    L.append("\n## Match predictions (scoreline + advancer)\n")
    L.append("| # | Tie | Pick | Advancer | Win% | EV |")
    L.append("|---|---|---|---|---|---|")
    for i, p in enumerate(mp, 1):
        m = p["tie"]
        winp = round(100 * max(p["p_home"], p["p_away"]))
        note = tie_notes.get((m.team1, m.team2))
        tie_txt = f"{m.team1} vs {m.team2}" + (f"<br>_{note}_" if note else "")
        L.append(f"| {i} | {tie_txt} | **{m.team1} {p['home']}-{p['away']} {m.team2}** "
                 f"| {p['adv']} | {winp}% | {p['ev']:.1f} |")
    n_top = len(r["top4"])
    tilted = sc.get("lead_shrink", 1.0) < 1.0
    basis = ("lead-protection: ranked by chalk-tilted score, EV shown" if tilted
             else "pure EV — the max_ev recommendation")
    L.append(f"\n## Topscorers — pick {n_top} ({basis})\n")
    if tilted:
        L.append("_Ranked to **mirror the chalk field**: the per-goal multiplier is compressed toward "
                 "the attacker's, so a high-EV but under-owned DEF/MID differential (a chaser's play) "
                 "won't outrank the star attackers the field owns. EV column = de-biased expected "
                 "points (non-attackers credited on P(≥1 goal), not raw per-goal EV)._\n")
    L.append("| Player | Team | Pos | Opp | Goals | Src | EV |")
    L.append("|---|---|---|---|---|---|---|")
    for c in r["top4"]:
        L.append(_ts_row(c, mp))
    L.append("\n_📈 = anytime-goalscorer market · 📊 = blended · ✍️ = model g90 (form-blended) + opponent + penalty._\n")
    L.append(f"\n### Alternative: match-diversified {n_top} (same EV approach, ≤1 per tie — slightly lower variance)\n")
    L.append("| Player | Team | Pos | Opp | Goals | Src | EV |")
    L.append("|---|---|---|---|---|---|---|")
    for c in r["diversified"]:
        L.append(_ts_row(c, mp))
    L.append("\n### Next best\n")
    for c in r["ranked"][n_top:n_top + 6]:
        L.append(f"- {c['name']} ({c['team']}, {c['position']}, vs {_opp_label(c['team'], mp)}) — EV {c['ko_ev']:.1f}")
    L.append("\n> Cross-check: market odds already price form/injuries; coin-flips and any bracket "
             "reversals are reflected in the win% column. Confirm orientation + starters in-app before "
             "the lock.\n")
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    rows = ["type,item,detail,advancer,ev"]
    for p in mp:
        m = p["tie"]
        rows.append(f'match,"{m.team1} vs {m.team2}",{p["home"]}-{p["away"]},{p["adv"]},{p["ev"]:.1f}')
    for c in r["top4"]:
        rows.append(f'topscorer,"{c["name"]} ({c["team"]}, {c["position"]})",vs {_opp_label(c["team"], mp)},,{c["ko_ev"]:.1f}')
    with open(os.path.join(out_dir, "picks.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


def main(argv=None):
    import argparse

    from scorito.data import knockout_fixtures as kf
    p = argparse.ArgumentParser(description="Scorito WC2026 knockout pick optimizer (max_ev)")
    p.add_argument("--round", choices=["r32", "r16", "qf"], default="r32",
                   help="which knockout round (selects bracket + scoring)")
    p.add_argument("--odds-key", default=None, help="The Odds API key (live h2h+totals for the ties)")
    p.add_argument("--odds-file", default=None, help="replay a saved odds JSON instead of fetching")
    p.add_argument("--atgs", action="store_true", help="also pull anytime-goalscorer odds (needs --odds-key)")
    p.add_argument("--atgs-file", default=None, help="replay a saved ATGS JSON")
    p.add_argument("--results-file", default="data/cache/worldcup2026_results.json")
    p.add_argument("--out", default=None, help="output dir (default out/ko_<round>)")
    args = p.parse_args(argv)
    bundles = {
        "r32": dict(ties=kf.R32_TIES, round_name="Round of 32", alive_teams=kf.ALIVE_TEAMS,
                    injured_out=kf.INJURED_OUT, start_overrides=kf.R32_START_OVERRIDES,
                    tie_notes=kf.TIE_NOTES, standings=None),
        "r16": dict(ties=kf.R16_TIES, round_name="Round of 16", alive_teams=kf.R16_ALIVE_TEAMS,
                    injured_out=kf.R16_INJURED_OUT, start_overrides=kf.R16_START_OVERRIDES,
                    tie_notes=kf.R16_TIE_NOTES, standings=kf.STANDINGS),
        "qf": dict(ties=kf.QF_TIES, round_name="Quarterfinal", alive_teams=kf.QF_ALIVE_TEAMS,
                   injured_out=kf.QF_INJURED_OUT, start_overrides=kf.QF_START_OVERRIDES,
                   tie_notes=kf.QF_TIE_NOTES, standings=kf.STANDINGS),
    }
    r = run_knockout(odds_key=args.odds_key, odds_file=args.odds_file, atgs=args.atgs,
                     atgs_file=args.atgs_file, results_file=args.results_file, out_dir=args.out,
                     **bundles[args.round])
    out_dir = args.out or f"out/ko_{args.round}"
    print(f"Wrote {out_dir}/report.md and {out_dir}/picks.csv")
    print(f"Goal model: {'market odds + Elo' if r['used_odds'] else 'Elo only'} "
          f"({r['odds_coverage'][0]}/{r['odds_coverage'][1]} priced)")
    print("Scorelines:", ", ".join(f"{p['tie'].team1} {p['home']}-{p['away']} {p['tie'].team2}"
                                    for p in r["match_picks"][:4]), "...")
    print("Topscorers:", ", ".join(c["name"] for c in r["top4"]))


if __name__ == "__main__":
    main()
