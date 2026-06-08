"""Actual results from an openfootball-format JSON (scores fill in as matches play)."""
import json

from scorito.model.group_sim import _award, _rank_table


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def played_results(path):
    """``{(team1, team2): (home_goals, away_goals)}`` for matches that have a final score."""
    out = {}
    for m in _load(path).get("matches", []):
        ft = (m.get("score") or {}).get("ft")
        if ft and len(ft) == 2:
            out[(m["team1"], m["team2"])] = (int(ft[0]), int(ft[1]))
    return out


def actual_group_tables(path):
    """``{group: [team,...]}`` final tables, only for groups whose 6 matches all have scores."""
    groups = {}
    for m in _load(path).get("matches", []):
        grp = (m.get("group") or "").replace("Group ", "").strip()
        if not grp:
            continue
        groups.setdefault(grp, []).append(m)
    tables = {}
    for grp, ms in groups.items():
        played = [(m, (m.get("score") or {}).get("ft")) for m in ms]
        if len(ms) != 6 or any(ft is None for _, ft in played):
            continue  # group incomplete
        teams = []
        for m in ms:
            for t in (m["team1"], m["team2"]):
                if t not in teams:
                    teams.append(t)
        stats = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
        res = {}
        for m, ft in played:
            res[(m["team1"], m["team2"])] = (int(ft[0]), int(ft[1]))
            _award(stats[m["team1"]], stats[m["team2"]], int(ft[0]), int(ft[1]))
        tables[grp] = _rank_table(stats, h2h=res, rng=None)
    return tables
