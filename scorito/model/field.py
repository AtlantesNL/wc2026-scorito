"""Generate plausible rival pool entries by sampling each pick from chalk-weighted
distributions. One ``sharpness`` exponent controls chalkiness (0 = ~uniform, higher =
piles onto favourites/modal scores). No pool data exists -> this is an explicit, tunable
assumption."""
import numpy as np


def _sharp_probs(weights, sharpness):
    w = np.asarray(weights, dtype=float) ** sharpness
    s = w.sum()
    return w / s if s > 0 else np.full(len(w), 1.0 / len(w))


def generate_field(n, scoreline_choices, champion_probs, topscorer_pool, sharpness, rng):
    """``scoreline_choices``: {(home,away): [(scoreline, exact_prob), ...]}.
    ``champion_probs``: {team: P(win)}. ``topscorer_pool``: [(candidate_dict, ev), ...].
    Returns a list of ``n`` entries {scorelines, champion, topscorers}."""
    teams = list(champion_probs)
    champ_p = _sharp_probs([champion_probs[t] for t in teams], sharpness)
    ts_cands = [c for c, _ in topscorer_pool]
    ts_p = _sharp_probs([ev for _, ev in topscorer_pool], sharpness)
    match_opts = {k: ([s for s, _ in v], _sharp_probs([p for _, p in v], sharpness))
                  for k, v in scoreline_choices.items()}

    entries = []
    for _ in range(n):
        scorelines = {}
        for k, (opts, p) in match_opts.items():
            scorelines[k] = opts[rng.choice(len(opts), p=p)]
        champion = teams[rng.choice(len(teams), p=champ_p)]
        idxs = rng.choice(len(ts_cands), size=6, replace=False, p=ts_p)
        topscorers = [ts_cands[i] for i in idxs]
        entries.append(dict(scorelines=scorelines, champion=champion, topscorers=topscorers))
    return entries
