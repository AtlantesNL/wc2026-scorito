"""Pool-win engine: sample tournament worlds, score entries, and choose the champion that
maximizes P(our entry finishes strictly 1st) against a modelled field. Reuses the goals
grids, the tournament bracket helpers, and eval/metrics."""
import numpy as np

from scorito import config
from scorito.model.bracket import ThirdSlot, assign_thirds, qualify_thirds
from scorito.model.group_sim import _award, _rank_table, _sample_scores
from scorito.model.topscorers import sample_player_goals
from scorito.model.tournament import _resolve, advance_matrix


def _grp_matches(gteams, group_matches):
    out = {g: [] for g in gteams}
    for (a, b) in group_matches:
        for g, ts in gteams.items():
            if a in ts and b in ts:
                out[g].append((a, b))
                break
    return out


def sample_worlds(gteams, group_matches, grids, elo, bracket, candidates,
                  team_factors, sims=config.POOL_WIN_SIMS, seed=0):
    """List of ``sims`` worlds: {scores:{(a,b):(h,a)}, place:{group:[teams]}, champion, pgoals:{name:int}}."""
    rng = np.random.default_rng(seed)
    all_teams = sorted({t for ts in gteams.values() for t in ts})
    P = advance_matrix(all_teams, elo)
    sampled = _sample_scores(group_matches, grids, sims, rng)
    pgoals = sample_player_goals(candidates, team_factors, sims, rng)
    grp = _grp_matches(gteams, group_matches)
    slot_locs = [(m.num, side, ref.allowed) for m in bracket
                 for side, ref in (("t1", m.team1), ("t2", m.team2)) if isinstance(ref, ThirdSlot)]

    worlds = []
    for s in range(sims):
        scores = {k: (int(sampled[k][0][s]), int(sampled[k][1][s])) for k in group_matches}
        place, thirds = {}, []
        for g, ts in gteams.items():
            stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
            h2h = {}
            for (a, b) in grp[g]:
                ga, gb = scores[(a, b)]
                h2h[(a, b)] = (ga, gb)
                _award(stats[a], stats[b], ga, gb)
            order = _rank_table(stats, h2h=h2h, rng=rng)
            place[g] = order
            if len(order) >= 3:
                thirds.append(dict(team=order[2], group=g, **stats[order[2]]))
        slot_team = {}
        if slot_locs:
            assigned = assign_thirds(qualify_thirds(thirds), [a for (_, _, a) in slot_locs])
            for j, (num, side, _) in enumerate(slot_locs):
                if j in assigned:
                    slot_team[(num, side)] = assigned[j]["team"]
        winners, losers = {}, {}
        champion = None
        for m in bracket:
            t1 = _resolve(m.team1, place, slot_team, winners, losers, m.num, "t1")
            t2 = _resolve(m.team2, place, slot_team, winners, losers, m.num, "t2")
            w_, l_ = (t1, t2) if rng.random() < P[(t1, t2)] else (t2, t1)
            winners[m.num], losers[m.num] = w_, l_
            if m.round == "Final":
                champion = w_
        worlds.append(dict(scores=scores, place=place, champion=champion,
                           pgoals={n: int(pgoals[n][s]) for n in pgoals}))
    return worlds
