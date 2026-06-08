"""Replay past tournaments through the Elo->grid model, score calibration, and sweep
the three tunable constants under leave-one-tournament-out cross-validation."""
import itertools

from scorito.eval import metrics
from scorito.model.goals import goals_from_elo
from scorito.model.grid import build_grid


def _predict(match, c):
    lam1, lam2 = goals_from_elo(match["home_pre"], match["away_pre"],
                                total=c["total"], divisor=c["divisor"])
    g = build_grid(lam1, lam2, rho=c["rho"])
    return [g.p_home, g.p_draw, g.p_away], g


def _outcome_idx(hg, ag):
    return 0 if hg > ag else (1 if hg == ag else 2)


def evaluate(matches, c):
    """Mean 1X2 log-loss + Brier + reliability over ``matches`` for constants ``c``."""
    ll = br = 0.0
    rel = []
    for m in matches:
        probs, _ = _predict(m, c)
        idx = _outcome_idx(m["hg"], m["ag"])
        ll += metrics.log_loss(probs, idx)
        br += metrics.brier(probs, idx)
        rel.append((probs[0], idx == 0))
    n = max(1, len(matches))
    return {"logloss_1x2": ll / n, "brier_1x2": br / n,
            "reliability": metrics.reliability_bins(rel), "n": len(matches)}


def _grid_best(datasets, grids):
    """Constants minimising mean per-tournament 1X2 log-loss over ``datasets``."""
    best = None
    for rho, total, divisor in itertools.product(grids["rho"], grids["total"], grids["divisor"]):
        c = dict(rho=rho, total=total, divisor=divisor)
        ll = sum(evaluate(datasets[lab], c)["logloss_1x2"] for lab in datasets) / len(datasets)
        if best is None or ll < best["logloss"]:
            best = dict(c, logloss=ll)
    return best


def sweep(datasets, grids):
    """Grid-best constants on ALL data, plus an HONEST out-of-sample ``cv_logloss`` from
    leave-one-tournament-out CV: each fold re-fits the grid on the *other* tournaments
    and scores the held-out one. (Single tournament -> degenerates to in-sample.)"""
    labels = list(datasets)
    per_fold = {}
    for held in labels:
        train = {k: v for k, v in datasets.items() if k != held} or datasets
        bt = _grid_best(train, grids)
        c = dict(rho=bt["rho"], total=bt["total"], divisor=bt["divisor"])
        per_fold[held] = evaluate(datasets[held], c)["logloss_1x2"]
    final = _grid_best(datasets, grids)
    return dict(rho=final["rho"], total=final["total"], divisor=final["divisor"],
                cv_logloss=sum(per_fold.values()) / len(per_fold), per_fold=per_fold)
