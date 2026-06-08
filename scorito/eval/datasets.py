"""Past-tournament datasets from the martj42 international-results CSV, annotated with
self-computed pre-match Elo (warmed up on all prior matches).

Source CSV: https://raw.githubusercontent.com/martj42/international_results/master/results.csv
columns: date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
(verify the header on first fetch; cache to data/cache/history/intl_results.csv)."""
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
