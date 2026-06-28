"""Pure evaluation metrics: probabilistic accuracy + realized Scorito points."""
import math

from scorito import config

_EPS = 1e-15


def log_loss(probs, outcome_idx: int) -> float:
    """Negative log of the probability assigned to the realised outcome (clamped)."""
    p = min(1.0, max(_EPS, probs[outcome_idx]))
    return -math.log(p)


def brier(probs, outcome_idx: int) -> float:
    """Sum of squared error vs the one-hot outcome."""
    return sum((p - (1.0 if i == outcome_idx else 0.0)) ** 2 for i, p in enumerate(probs))


def reliability_bins(pairs, nbins: int = 10):
    """``pairs`` = [(predicted_prob, outcome_bool)]. Returns one (mean_pred, mean_obs,
    count) tuple per equal-width bin; empty bins are (None, None, 0)."""
    buckets = [[] for _ in range(nbins)]
    for p, o in pairs:
        idx = min(nbins - 1, max(0, int(p * nbins)))
        buckets[idx].append((p, 1.0 if o else 0.0))
    out = []
    for b in buckets:
        if b:
            out.append((sum(x[0] for x in b) / len(b),
                        sum(x[1] for x in b) / len(b), len(b)))
        else:
            out.append((None, None, 0))
    return out


def _sign(h, a) -> int:
    return (h > a) - (h < a)


def match_points(pick, actual, pts_exact: int = config.PTS_EXACT,
                 pts_toto: int = config.PTS_TOTO) -> int:
    """Exact pays ``pts_exact``, else ``pts_toto`` if the 1/X/2 outcome matches, else 0.
    Defaults = group phase (45/30); pass 90/60 to grade a knockout round."""
    if tuple(pick) == tuple(actual):
        return pts_exact
    if _sign(*pick) == _sign(*actual):
        return pts_toto
    return 0


def standings_points(predicted_table, actual_table) -> int:
    """25 per team whose predicted finishing position matches the actual one."""
    return config.PTS_POSITION * sum(
        1 for p, a in zip(predicted_table, actual_table) if p == a
    )


def topscorer_points(picks, scorer_goals) -> int:
    """Sum of goals x position multiplier (ATT 8 / MID 16 / DEF,GK 32) over our picks."""
    return sum(int(scorer_goals.get(c["name"], 0)) * config.TOPSCORER_MULT[c["position"]]
               for c in picks)
