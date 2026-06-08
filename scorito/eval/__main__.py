"""CLI: python -m scorito.eval scorecard|calibrate"""
import argparse
import re

from scorito import config as cfg
from scorito.eval import calibrate as cal
from scorito.eval import datasets as ds
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


def _calibrate(args):
    labels = args.tournaments.split(",") if args.tournaments else list(ds.TOURNAMENTS)
    data = {}
    for lab in labels:
        tour, years = ds.TOURNAMENTS[lab]
        data[lab] = ds.load_tournament(args.results_csv, tour, years)["eval_matches"]
    grids = dict(rho=[0.0, 0.001, 0.01], total=[2.4, 2.6, 2.8],
                 divisor=[150.0, 200.0, 250.0, 300.0, 400.0])
    current = dict(rho=cfg.DC_RHO, total=cfg.NEUTRAL_AVG_TOTAL, divisor=cfg.ELO_GOAL_DIVISOR)
    base = cal.sweep(data, {k: [current[k]] for k in current})
    best = cal.sweep(data, grids)
    print(f"current  cv_logloss={base['cv_logloss']:.4f}  {current}")
    print(f"optimal  cv_logloss={best['cv_logloss']:.4f}  "
          f"rho={best['rho']} total={best['total']} divisor={best['divisor']}")
    print(f"per-fold: { {k: round(v, 4) for k, v in best['per_fold'].items()} }")
    if args.write:
        _write_constants(best)
        print("Wrote DC_RHO / NEUTRAL_AVG_TOTAL / ELO_GOAL_DIVISOR to scorito/config.py")


def _write_constants(best):
    path = "scorito/config.py"
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    txt = re.sub(r"DC_RHO = [\d.]+", f"DC_RHO = {best['rho']}", txt)
    txt = re.sub(r"NEUTRAL_AVG_TOTAL = [\d.]+", f"NEUTRAL_AVG_TOTAL = {best['total']}", txt)
    txt = re.sub(r"ELO_GOAL_DIVISOR = [\d.]+", f"ELO_GOAL_DIVISOR = {best['divisor']}", txt)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)


def main():
    p = argparse.ArgumentParser(prog="scorito.eval")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scorecard")
    s.add_argument("--picks", default="out/picks.csv")
    s.add_argument("--results", default="data/cache/worldcup2026.json")
    s.add_argument("--scorers", default="data/wc2026_scorers.json")
    s.set_defaults(func=_scorecard)

    c = sub.add_parser("calibrate")
    c.add_argument("--results-csv", default="data/cache/history/intl_results.csv")
    c.add_argument("--tournaments", default="")
    c.add_argument("--write", action="store_true")
    c.set_defaults(func=_calibrate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
