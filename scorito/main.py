"""CLI + orchestration: fixtures -> Elo/odds -> grids -> group optimizer ->
champion + topscorers -> report. The Elo-only path (``--no-odds``) runs offline.
"""
import argparse
import json
import os
import warnings
from collections import defaultdict

from scorito import config
from scorito.data import elo, fixtures
from scorito.data import squads as squads_data
from scorito.data.fixtures import group_teams
from scorito.data.topscorer_candidates import CANDIDATES
from scorito.data.priors import blend_champion_probs, blended_probs
from scorito.model import bracket as bracket_mod
from scorito.model import tournament
from scorito.model.champion import recommend_champion
from scorito.model.goals import expected_goals
from scorito.model.grid import build_grid
from scorito.model.group_opt import optimize_group
from scorito.model.topscorers import pick_topscorers
from scorito.report import RunResult, write_report


def _default_fixtures():
    cached = "data/cache/worldcup2026.json"
    return cached if os.path.exists(cached) else fixtures.WORLDCUP_URL


def run(no_odds=True, pool_size=32, risk="balanced", odds_key=None, odds_file=None,
        out_dir="out", fixtures_src=None, sims=config.MC_SIMS, k=config.TOPK_SCORELINES, seed=0):
    matches = fixtures.load_fixtures(fixtures_src or _default_fixtures())
    gteams = group_teams(matches)
    all_teams = sorted({t for ts in gteams.values() for t in ts})
    elo_map = elo.get_elo(all_teams)  # clean ratings — used for the NEUTRAL knockout advance matrix
    # Host advantage applies to the hosts' GROUP games only (Elo fallback path); it must NOT leak
    # into the knockout sim (those venues aren't necessarily a given host's home — that bug
    # inflated host title odds, e.g. Mexico as a fake "contender").
    elo_group = dict(elo_map)
    for host in config.HOSTS:
        if host in elo_group:
            elo_group[host] += config.HOST_ELO_BONUS

    odds_map, used_odds = None, False
    if not no_odds and (odds_key or odds_file):
        from scorito.data import odds  # lazy: only needed when odds are requested
        raw = json.load(open(odds_file, encoding="utf-8")) if odds_file else odds.fetch_odds(odds_key)
        odds_map = odds.parse_odds(raw)
        used_odds = True

    toto_weight = config.scoreline_toto_weight(risk, pool_size)

    group_results = {}
    team_lambda = defaultdict(list)
    all_grids = {}
    for g, teams in gteams.items():
        gm = [m for m in matches if m.group == g]
        gmatches = [(m.team1, m.team2) for m in gm]
        grids = {}
        for m in gm:
            l1, l2 = expected_goals(m, odds_map, elo_group)
            grids[(m.team1, m.team2)] = build_grid(l1, l2)
            team_lambda[m.team1].append(l1)
            team_lambda[m.team2].append(l2)
        all_grids.update(grids)
        group_results[g] = optimize_group(teams, gmatches, grids, k=k, sims=sims,
                                          seed=seed, group=g, toto_weight=toto_weight)

    means = {t: sum(v) / len(v) for t, v in team_lambda.items()}
    avg = sum(means.values()) / len(means)
    team_factors = {t: means[t] / avg for t in means}

    # Champion P(win): full-tournament Monte-Carlo when the complete 12-group bracket is
    # present (blended with the market/Opta prior); otherwise (e.g. a partial-fixture test
    # run) fall back to the static prior.
    advance, pool_win, pool_win_stable = {}, {}, True
    group_match_keys = [(m.team1, m.team2) for m in matches]
    if len(gteams) == 12:
        brk = bracket_mod.load_bracket(fixtures_src or _default_fixtures())
        sim = tournament.simulate(gteams, group_match_keys, all_grids, elo_map, brk,
                                  sims=sims, seed=seed)
        pwin = blend_champion_probs(sim["win"], blended_probs())
        advance = sim["advance"]
    else:
        pwin = blended_probs()

    # Drop topscorer candidates not in their team's confirmed 2026 squad.
    squads = squads_data.load_squads()
    kept, dropped = squads_data.validate_candidates(CANDIDATES, squads)
    if dropped:
        warnings.warn(
            "Topscorer candidates dropped (not in confirmed squad): "
            + ", ".join(f"{c['name']} ({c['team']})" for c in dropped)
        )

    topscorers = pick_topscorers(team_factors, n=config.TOPSCORER_SLOTS, risk=risk, candidates=kept)
    champion = recommend_champion(pwin, pool_size, risk)

    # Pool-win: pick the champion that maximizes P(finishing 1st) vs a modelled chalky field.
    if len(gteams) == 12:
        from scorito.model import pool
        from scorito.model.match_ev import topk_scorelines
        from scorito.model.topscorers import score_candidate
        our_entry = {
            "scorelines": {(a, b): (s.home, s.away)
                           for gr in group_results.values()
                           for (a, b), s in zip(gr.matches, gr.scorelines)},
            "champion": champion[0].team,
            "topscorers": topscorers,
        }
        scoreline_choices = {key: [((s.home, s.away), all_grids[key].exact(s.home, s.away))
                                   for s in topk_scorelines(all_grids[key], k=config.TOPK_SCORELINES)]
                             for key in all_grids}
        ts_pool = [(c, score_candidate(c, team_factors)) for c in kept]
        contenders = sorted({t for t, p in pwin.items() if p >= 0.02} | {champion[0].team})
        best, pool_win, pool_win_stable = pool.pool_win_champion(
            our_entry, gteams, group_match_keys, all_grids, elo_map, brk, kept,
            team_factors, pwin, scoreline_choices, ts_pool, pool_size, contenders, seed=seed)
        champion = sorted(champion, key=lambda r: (r.team != best, -pool_win.get(r.team, 0.0)))

    result = RunResult(
        groups=group_results,
        champion=champion,
        topscorers=topscorers,
        pool_size=pool_size, risk=risk, used_odds=used_odds,
        meta={"scoreline_toto_weight": toto_weight, "pool_win_stable": pool_win_stable,
              "pool_win_sims": config.POOL_WIN_SIMS},
        advance=advance,
        pool_win=pool_win,
    )
    write_report(result, out_dir)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description="Scorito WC2026 group-phase pick optimizer")
    p.add_argument("--no-odds", action="store_true", help="Elo-only, no API key needed")
    p.add_argument("--odds-key", default=None, help="The Odds API key (enables market odds)")
    p.add_argument("--odds-file", default=None, help="Load a saved Odds API JSON instead of fetching")
    p.add_argument("--pool-size", type=int, default=32)
    p.add_argument("--risk", choices=["max_ev", "balanced", "aggressive"], default="balanced")
    p.add_argument("--out", default="out")
    p.add_argument("--sims", type=int, default=config.MC_SIMS)
    args = p.parse_args(argv)

    no_odds = args.no_odds or not (args.odds_key or args.odds_file)
    res = run(no_odds=no_odds, pool_size=args.pool_size, risk=args.risk,
              odds_key=args.odds_key, odds_file=args.odds_file, out_dir=args.out, sims=args.sims)

    print(f"Wrote {args.out}/report.md and {args.out}/picks.csv")
    print(f"Goal model: {'market odds + Elo' if res.used_odds else 'Elo only'}")
    print(f"Expected group-phase points (model): {res.expected_group_points:.0f}")
    print(f"Champion: {res.champion[0].team} (alt: {res.champion[1].team})")
    print("Topscorers:", ", ".join(c["name"] for c in res.topscorers))


if __name__ == "__main__":
    main()
