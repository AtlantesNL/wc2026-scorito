"""Champion pick with a pool-leverage adjustment.

EV of a champion pick is simply ``P(win) * 250``. But in a pool you don't want
expected points — you want to *win the pool*, which means avoiding the over-owned
favourite. We estimate each team's pick-share (a sharpened version of its win
probability — pools pile onto favourites) and divide the value by how crowded the
pick is, with the penalty growing in pool size and risk appetite.

- max_ev    -> pure P(win) (ignore the crowd)
- balanced  -> moderate fade of crowded picks
- aggressive-> strong fade (only sensible in large pools)
"""
from dataclasses import dataclass

from scorito import config
from scorito.data.priors import blended_probs

GAMMA = {"max_ev": 0.0, "balanced": 0.5, "aggressive": 1.0}


@dataclass
class ChampionRec:
    team: str
    p_win: float
    ev_points: float
    est_share: float
    leverage: float


def est_shares(pwin: dict[str, float], temp: float = 0.7) -> dict[str, float]:
    """Fraction of the pool expected to pick each team (sharpened, normalized)."""
    raw = {t: p ** (1.0 / temp) for t, p in pwin.items()}
    s = sum(raw.values())
    return {t: raw[t] / s for t in raw}


def leverage_score(p_win: float, share: float, pool_size: int, risk: str) -> float:
    g = GAMMA.get(risk, 0.5)
    return p_win / (1.0 + share * (pool_size - 1)) ** g


def recommend_champion(pool_size: int, risk: str = "balanced"):
    """Return ChampionRecs sorted by pool-adjusted leverage (best first)."""
    pwin = blended_probs()
    shares = est_shares(pwin)
    recs = [
        ChampionRec(
            team=t,
            p_win=p,
            ev_points=p * config.CHAMPION_BONUS,
            est_share=shares[t],
            leverage=leverage_score(p, shares[t], pool_size, risk),
        )
        for t, p in pwin.items()
    ]
    recs.sort(key=lambda r: r.leverage, reverse=True)
    return recs
