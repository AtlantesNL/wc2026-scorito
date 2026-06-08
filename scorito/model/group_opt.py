"""Joint group optimizer: choose 6 scorelines that maximize

    total = Σ match-EV(scoreline)  +  Σ_pos 25 · P(predicted team at pos finishes there)

The standings term couples all six matches, because Scorito derives the group
table from *your* predicted scores. We enumerate the top-K scorelines per match
(K⁶ combos), derive each combo's predicted table deterministically, score it
against the Monte-Carlo position probabilities, and keep the best. ``score_combo``
is a pure function so the objective can be unit-tested without simulation.
"""
import itertools
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from scorito import config
from scorito.model.group_sim import _award, _rank_table, position_probs
from scorito.model.match_ev import topk_scorelines


@dataclass
class GroupResult:
    group: str
    teams: list
    matches: list           # list of (team1, team2)
    scorelines: list        # aligned with `matches`
    predicted_standing: list
    match_pts: float
    stand_pts: float
    total: float
    naive_total: float

    @property
    def picks(self):
        return list(zip(self.matches, self.scorelines))


def predicted_standing(scorelines, matches, teams):
    """Deterministic group table derived from a set of predicted scorelines."""
    stats = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
    results = {}
    for (a, b), s in zip(matches, scorelines):
        results[(a, b)] = (s.home, s.away)
        _award(stats[a], stats[b], s.home, s.away)
    return _rank_table(stats, h2h=results, rng=None)


def score_combo(scorelines, matches, teams, probs):
    """Joint objective for one combination of scorelines.

    Returns ``(match_pts, stand_pts, total, predicted_order)``.
    """
    match_pts = sum(s.ev for s in scorelines)
    order = predicted_standing(scorelines, matches, teams)
    stand_pts = sum(config.PTS_POSITION * float(probs[order[p]][p]) for p in range(len(teams)))
    return match_pts, stand_pts, match_pts + stand_pts, order


def standings_only_ordering(probs):
    """Hungarian assignment: ordering that maximizes Σ P(team at its position).

    Used as a cross-check on the standings component (the enumerator must never
    do worse than this on standings when match EV is held equal).
    """
    teams = list(probs.keys())
    P = np.array([probs[t] for t in teams])
    rows, cols = linear_sum_assignment(-P)
    pos_to_team = {int(c): teams[int(r)] for r, c in zip(rows, cols)}
    return [pos_to_team[p] for p in range(len(teams))]


def optimize_group(teams, matches, grids, k=config.TOPK_SCORELINES,
                   sims=config.MC_SIMS, seed=0, probs=None, group=""):
    if probs is None:
        probs = position_probs(teams, matches, grids, sims=sims, seed=seed)
    cand = [topk_scorelines(grids[m], k) for m in matches]
    naive = [c[0] for c in cand]
    _, _, naive_total, _ = score_combo(naive, matches, teams, probs)

    best = None
    for combo in itertools.product(*cand):
        combo = list(combo)
        mp, sp, total, order = score_combo(combo, matches, teams, probs)
        if best is None or total > best["total"]:
            best = dict(scorelines=combo, order=order, match_pts=mp, stand_pts=sp, total=total)

    return GroupResult(
        group=group, teams=list(teams), matches=list(matches),
        scorelines=best["scorelines"], predicted_standing=best["order"],
        match_pts=best["match_pts"], stand_pts=best["stand_pts"],
        total=best["total"], naive_total=naive_total,
    )
