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
    print(f"TOTAL (ex-champion): ours {total} "
          f"vs always-1-0+chalk {line['baseline_1_0'] + stand['ours']}")


def main():
    p = argparse.ArgumentParser(prog="scorito.eval")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scorecard")
    s.add_argument("--picks", default="out/picks.csv")
    s.add_argument("--results", default="data/cache/worldcup2026.json")
    s.add_argument("--scorers", default="data/wc2026_scorers.json")
    s.set_defaults(func=_scorecard)
    # calibrate subcommand wired in Phase 2 (Task 10)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
