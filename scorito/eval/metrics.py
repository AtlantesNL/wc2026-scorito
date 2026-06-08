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
