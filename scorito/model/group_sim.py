"""Monte-Carlo group simulation -> probability each team finishes 1st..4th.

Tiebreakers follow the FIFA World Cup 2026 group order: (1) points, (2) overall
goal difference, (3) overall goals for, then among teams still level (4) head-to-
head points, (5) h2h goal difference, (6) h2h goals for, then a coin toss
(``rng``) standing in for fair-play / drawing of lots. With ``rng=None`` residual
ties resolve deterministically by team order (used to derive a fixed predicted
standing in the optimizer).
"""
import numpy as np

from scorito import config


def _award(sa, sb, ga, gb):
    sa["gf"] += ga
    sb["gf"] += gb
    sa["gd"] += ga - gb
    sb["gd"] += gb - ga
    if ga > gb:
        sa["pts"] += 3
    elif gb > ga:
        sb["pts"] += 3
    else:
        sa["pts"] += 1
        sb["pts"] += 1


def _key(s):
    return (s["pts"], s["gd"], s["gf"])


def _clusters(teams, keyfn):
    """Yield consecutive runs of teams sharing an identical key (teams pre-sorted)."""
    i = 0
    while i < len(teams):
        j = i + 1
        while j < len(teams) and keyfn(teams[j]) == keyfn(teams[i]):
            j += 1
        yield teams[i:j]
        i = j


def _break_cluster(cluster, h2h, rng):
    if not h2h or len(cluster) == 1:
        out = list(cluster)
        if len(out) > 1 and rng is not None:
            rng.shuffle(out)
        return out
    cset = set(cluster)
    mini = {t: {"pts": 0, "gd": 0, "gf": 0} for t in cluster}
    for (a, b), (ga, gb) in h2h.items():
        if a in cset and b in cset:
            _award(mini[a], mini[b], ga, gb)
    ordered = sorted(cluster, key=lambda t: _key(mini[t]), reverse=True)
    out = []
    for sub in _clusters(ordered, lambda t: _key(mini[t])):
        sub = list(sub)
        if len(sub) > 1 and rng is not None:
            rng.shuffle(sub)
        out.extend(sub)
    return out


def _rank_table(stats, h2h=None, rng=None):
    """Return teams ordered 1st..last per FIFA tiebreakers."""
    teams = sorted(stats.keys(), key=lambda t: _key(stats[t]), reverse=True)
    out = []
    for cluster in _clusters(teams, lambda t: _key(stats[t])):
        out.extend(_break_cluster(cluster, h2h, rng))
    return out


def _sample_scores(matches, grids, sims, rng):
    sampled = {}
    for key in matches:
        m = grids[key].matrix
        flat = m.ravel()
        flat = flat / flat.sum()
        idx = rng.choice(flat.size, size=sims, p=flat)
        gi, gj = np.divmod(idx, m.shape[0])
        sampled[key] = (gi, gj)
    return sampled


def position_probs(teams, matches, grids, sims=config.MC_SIMS, seed=0):
    """``{team: np.array([p1st, p2nd, p3rd, p4th])}``."""
    rng = np.random.default_rng(seed)
    sampled = _sample_scores(matches, grids, sims, rng)
    counts = {t: np.zeros(len(teams)) for t in teams}
    for s in range(sims):
        stats = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
        results = {}
        for (a, b) in matches:
            ga, gb = int(sampled[(a, b)][0][s]), int(sampled[(a, b)][1][s])
            results[(a, b)] = (ga, gb)
            _award(stats[a], stats[b], ga, gb)
        order = _rank_table(stats, h2h=results, rng=rng)
        for pos, t in enumerate(order):
            counts[t][pos] += 1
    return {t: counts[t] / sims for t in teams}
