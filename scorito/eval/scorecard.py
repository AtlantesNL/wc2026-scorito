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
