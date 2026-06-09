"""Full-tournament Monte-Carlo -> P(win) + advancement for all 48 teams.

Group matches are sampled from their (odds/Elo) grids; knockout ties use a precomputed
Elo advance matrix (no KO odds exist). Reuses the group-sim primitives."""
import numpy as np

from scorito import config
from scorito.model.bracket import (GroupPos, LoserOf, ThirdSlot, WinnerOf,
                                    assign_thirds, qualify_thirds)
from scorito.model.goals import goals_from_elo
from scorito.model.grid import build_grid
from scorito.model.group_sim import _award, _rank_table, _sample_scores

ROUND_NEXT = {
    "Round of 32": "r16",
    "Round of 16": "qf",
    "Quarter-final": "sf",
    "Semi-final": "final",
    "Final": "win",
}


def advance_matrix(teams, elo):
    """``{(A, B): P(A wins a KO tie vs B)}`` = p_win + 0.5*p_draw from a neutral Elo grid."""
    P = {}
    for i, a in enumerate(teams):
        for b in teams[i + 1:]:
            l1, l2 = goals_from_elo(elo.get(a, 1500.0), elo.get(b, 1500.0))
            g = build_grid(l1, l2)
            pa = g.p_home + 0.5 * g.p_draw
            P[(a, b)] = pa
            P[(b, a)] = 1.0 - pa
    return P


def _resolve(ref, place, slot_team, winners, losers, num, side):
    if isinstance(ref, GroupPos):
        return place[ref.group][ref.pos - 1]
    if isinstance(ref, ThirdSlot):
        return slot_team[(num, side)]
    if isinstance(ref, WinnerOf):
        return winners[ref.num]
    if isinstance(ref, LoserOf):
        return losers[ref.num]
    raise ValueError(f"Unresolvable ref {ref!r}")


def simulate(gteams, group_matches, group_grids, elo, bracket, sims=config.MC_SIMS, seed=0):
    """Monte-Carlo the whole tournament. Returns
    ``{"win": {team: P}, "advance": {team: {"r16","qf","sf","final","win": P}}}``."""
    rng = np.random.default_rng(seed)
    all_teams = sorted({t for ts in gteams.values() for t in ts})
    P = advance_matrix(all_teams, elo)
    sampled = _sample_scores(group_matches, group_grids, sims, rng)

    grp_matches = {g: [] for g in gteams}
    for (a, b) in group_matches:
        for g, ts in gteams.items():
            if a in ts and b in ts:
                grp_matches[g].append((a, b))
                break

    # third-place slots, in a fixed order, with their (match num, side) and allowed groups
    slot_locs = []
    for m in bracket:
        for side, ref in (("t1", m.team1), ("t2", m.team2)):
            if isinstance(ref, ThirdSlot):
                slot_locs.append((m.num, side, ref.allowed))

    adv = {t: dict(r16=0, qf=0, sf=0, final=0, win=0) for t in all_teams}
    for s in range(sims):
        place, thirds = {}, []
        for g, ts in gteams.items():
            stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
            h2h = {}
            for (a, b) in grp_matches[g]:
                ga, gb = int(sampled[(a, b)][0][s]), int(sampled[(a, b)][1][s])
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
        for m in bracket:
            t1 = _resolve(m.team1, place, slot_team, winners, losers, m.num, "t1")
            t2 = _resolve(m.team2, place, slot_team, winners, losers, m.num, "t2")
            if rng.random() < P[(t1, t2)]:
                w, l = t1, t2
            else:
                w, l = t2, t1
            winners[m.num], losers[m.num] = w, l
            key = ROUND_NEXT.get(m.round)
            if key:
                adv[w][key] += 1

    advance = {t: {k: adv[t][k] / sims for k in adv[t]} for t in all_teams}
    return {"win": {t: advance[t]["win"] for t in all_teams}, "advance": advance}
