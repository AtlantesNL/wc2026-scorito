"""Pool-win engine: sample tournament worlds, score entries, and choose the champion that
maximizes P(our entry finishes strictly 1st) against a modelled field. Reuses the goals
grids, the tournament bracket helpers, and eval/metrics."""
import numpy as np

from scorito import config
from scorito.eval.metrics import match_points, standings_points, topscorer_points
from scorito.model.bracket import ThirdSlot, assign_thirds, qualify_thirds
from scorito.model.field import generate_field
from scorito.model.group_sim import _award, _rank_table, _sample_scores
from scorito.model.topscorers import sample_player_goals, score_candidate
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


def predicted_tables(entry, gteams, grp_matches):
    """Standings each group implies from this entry's scorelines (Scorito derives the table
    from your scores)."""
    tables = {}
    for g, ts in gteams.items():
        stats = {t: dict(pts=0, gd=0, gf=0) for t in ts}
        h2h = {}
        for (a, b) in grp_matches[g]:
            ga, gb = entry["scorelines"][(a, b)]
            h2h[(a, b)] = (ga, gb)
            _award(stats[a], stats[b], ga, gb)
        tables[g] = _rank_table(stats, h2h=h2h, rng=None)
    return tables


def _entry_base(entry, pred_tables, world):
    """Non-champion points for one entry in one world (scorelines + standings + topscorers)."""
    pts = sum(match_points(entry["scorelines"][k], world["scores"][k]) for k in world["scores"]
              if k in entry["scorelines"])
    pts += sum(standings_points(pred_tables[g], world["place"][g]) for g in world["place"])
    pts += topscorer_points(entry["topscorers"], world["pgoals"])
    return pts


def score_field(our_entry, field, worlds, gteams, group_matches):
    """Returns (base_w[W], rival_base[N,W], rival_champ[N], champ_w[W])."""
    grp = _grp_matches(gteams, group_matches)
    W = len(worlds)
    our_pred = predicted_tables(our_entry, gteams, grp)
    base_w = np.array([_entry_base(our_entry, our_pred, w) for w in worlds], dtype=float)
    rival_base = np.zeros((len(field), W))
    for r, e in enumerate(field):
        rp = predicted_tables(e, gteams, grp)
        rival_base[r] = [_entry_base(e, rp, w) for w in worlds]
    rival_champ = [e["champion"] for e in field]
    champ_w = np.array([w["champion"] for w in worlds], dtype=object)
    return base_w, rival_base, rival_champ, champ_w


def champion_win_probs(base_w, rival_base, rival_champ, champ_w, candidates,
                       bonus=config.CHAMPION_BONUS):
    """P(our entry finishes strictly 1st) for each candidate champion, holding our other picks
    fixed. ``base_w`` is our non-champion score per world; the field is fixed."""
    if rival_base.shape[0] == 0:
        return {c: 1.0 for c in candidates}
    rc = np.array(rival_champ, dtype=object)[:, None]
    rival_total = rival_base + bonus * (rc == champ_w[None, :])
    max_rival = rival_total.max(axis=0)
    return {c: float(np.mean(base_w + bonus * (champ_w == c) > max_rival)) for c in candidates}


def greedy_topscorers(our_fixed, max_rival, points_by_name, n_slots):
    """Select n_slots names maximizing P(our_fixed + sum_picked > max_rival), tie-broken by expected
    points (so a fieldless max_rival=-inf reduces to EV-greedy). Greedy forward-select, then a
    coordinate-ascent swap pass that fires only on strict pool-win gains. our_fixed[W], max_rival[W]
    numpy; points_by_name {name: ndarray(W)} = multiplier*goals. Returns (picked_names, pool_win)."""
    names = list(points_by_name)

    def pwin(w):
        return float(np.mean(our_fixed + w > max_rival))

    chosen, ts_w = [], np.zeros_like(our_fixed, dtype=float)
    for _ in range(min(n_slots, len(names))):
        best = max((n for n in names if n not in chosen),
                   key=lambda n: (pwin(ts_w + points_by_name[n]), float(points_by_name[n].sum())))
        chosen.append(best)
        ts_w = ts_w + points_by_name[best]
    improved = True
    while improved:
        improved = False
        for i in range(len(chosen)):
            base = ts_w - points_by_name[chosen[i]]
            options = [n for n in names if n == chosen[i] or n not in chosen]
            best = max(options, key=lambda n: (pwin(base + points_by_name[n]),
                                               float(points_by_name[n].sum())))
            if best != chosen[i] and pwin(base + points_by_name[best]) > pwin(ts_w) + 1e-12:
                ts_w = base + points_by_name[best]
                chosen[i] = best
                improved = True
    return chosen, pwin(ts_w)


def pool_win_topscorers(our_entry, our_champion, candidates, gteams, group_matches, grids, elo,
                        bracket, team_factors, champion_probs, scoreline_choices, ts_field_pool,
                        pool_size, n_slots=config.TOPSCORER_SLOTS, seed=0, sims=config.POOL_WIN_SIMS,
                        bonus=config.CHAMPION_BONUS, baseline_names=None):
    """Pick n_slots topscorers maximizing P(our entry finishes 1st), holding scorelines + champion
    fixed, against a fame-weighted field. Returns (picks: candidate dicts with 'ev', pool_win).
    ``baseline_names`` (e.g. the EV+reserve pick) is evaluated too and kept if the greedy search
    can't strictly beat it — so the engine never ships worse picks than the baseline."""
    worlds = sample_worlds(gteams, group_matches, grids, elo, bracket, candidates, team_factors,
                           sims=sims, seed=seed)
    field = generate_field(max(0, pool_size - 1), scoreline_choices, champion_probs, ts_field_pool,
                           config.FIELD_SHARPNESS, np.random.default_rng(seed + 1))
    base_excl, rival_base, rival_champ, champ_w = score_field(
        dict(our_entry, topscorers=[]), field, worlds, gteams, group_matches)
    W = len(worlds)
    if rival_base.shape[0] == 0:
        max_rival = np.full(W, -np.inf)
    else:
        rc = np.array(rival_champ, dtype=object)[:, None]
        max_rival = (rival_base + bonus * (rc == champ_w[None, :])).max(axis=0)
    our_fixed = base_excl + bonus * (champ_w == our_champion)
    pgoals_arr = {n: np.array([w["pgoals"][n] for w in worlds], dtype=float) for n in worlds[0]["pgoals"]}
    points = {c["name"]: config.TOPSCORER_MULT[c["position"]] * pgoals_arr[c["name"]] for c in candidates}
    names, pwin = greedy_topscorers(our_fixed, max_rival, points, n_slots)
    if baseline_names is not None:
        bw = np.zeros(W)
        for n in baseline_names:
            if n in points:
                bw = bw + points[n]
        bp = float(np.mean(our_fixed + bw > max_rival))
        if bp > pwin:                       # greedy stuck below the baseline -> keep the baseline
            names, pwin = list(baseline_names), bp
    by_name = {c["name"]: c for c in candidates}
    picks = [dict(by_name[n], ev=round(score_candidate(by_name[n], team_factors), 3)) for n in names]
    return picks, pwin


def _best_with_floor(win_probs, champion_probs, eps=0.005):
    """Argmax of pool-win probability, breaking near-ties (within ``eps``) toward the higher
    outright P(win) — among similarly-leveraged champions, take the higher floor (which also
    lowers our own outcome variance). Avoids chasing Monte-Carlo noise on a flat landscape."""
    top = max(win_probs.values())
    near = [t for t in win_probs if win_probs[t] >= top - eps]
    return max(near, key=lambda t: champion_probs.get(t, 0.0))


def pool_win_champion(our_entry, gteams, group_matches, grids, elo, bracket, candidates,
                      team_factors, champion_probs, scoreline_choices, topscorer_pool,
                      pool_size, candidate_champions, seed=0,
                      sims=config.POOL_WIN_SIMS, sharpnesses=(1.5, 2.0, 3.0)):
    """Pick the champion maximizing P(our entry finishes 1st). Returns
    (best_champion, {champion: P(win) at default sharpness}, stable) where ``stable`` is True
    iff the argmax agrees across the ``sharpnesses`` sensitivity sweep. Worlds are sampled once
    and reused across sharpnesses; only the modelled field changes."""
    worlds = sample_worlds(gteams, group_matches, grids, elo, bracket, candidates,
                           team_factors, sims=sims, seed=seed)
    n_rivals = max(0, pool_size - 1)
    probs_by_sh = {}
    for sh in sharpnesses:
        field = generate_field(n_rivals, scoreline_choices, champion_probs,
                               topscorer_pool, sh, np.random.default_rng(seed + 1))
        base_w, rival_base, rival_champ, champ_w = score_field(
            our_entry, field, worlds, gteams, group_matches)
        probs_by_sh[sh] = champion_win_probs(base_w, rival_base, rival_champ, champ_w,
                                             candidate_champions)
    default_sh = (config.FIELD_SHARPNESS if config.FIELD_SHARPNESS in probs_by_sh
                  else sorted(probs_by_sh)[len(probs_by_sh) // 2])
    default_probs = probs_by_sh[default_sh]
    top = max(default_probs.values())
    eps = 2.0 * (top * (1.0 - top) / max(1, sims)) ** 0.5   # ~2 Monte-Carlo standard errors
    argmaxes = [_best_with_floor(probs_by_sh[sh], champion_probs, eps) for sh in sharpnesses]
    best = _best_with_floor(default_probs, champion_probs, eps)
    return best, default_probs, len(set(argmaxes)) == 1
