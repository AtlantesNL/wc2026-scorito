"""Assemble the human-readable report (report.md) and a transcription CSV."""
import csv
import os
from dataclasses import dataclass, field


@dataclass
class RunResult:
    groups: dict           # group letter -> GroupResult
    champion: list         # list of ChampionRec (sorted best-first)
    topscorers: list       # list of candidate dicts (with "ev")
    pool_size: int
    risk: str
    used_odds: bool
    meta: dict = field(default_factory=dict)

    @property
    def expected_group_points(self):
        return sum(g.total for g in self.groups.values())


def build_csv_rows(groups, champion, topscorers):
    """Uniform-schema rows: type, group, item, detail, value."""
    rows = []
    for g in sorted(groups):
        gr = groups[g]
        for (a, b), s in zip(gr.matches, gr.scorelines):
            rows.append(dict(type="match", group=g, item=f"{a} vs {b}",
                             detail=f"{s.home}-{s.away}", value=round(s.ev, 2)))
        for pos, team in enumerate(gr.predicted_standing, start=1):
            rows.append(dict(type="standing", group=g, item=f"{pos}. {team}",
                             detail="", value=""))
    for r in champion[:3]:
        rows.append(dict(type="champion", group="", item=r.team,
                         detail=f"p_win={r.p_win:.3f} share={r.est_share:.2f}",
                         value=round(r.ev_points, 1)))
    for c in topscorers:
        rows.append(dict(type="topscorer", group="", item=f"{c['name']} ({c['team']}, {c['position']})",
                         detail="PEN" if c.get("pen_taker") else "", value=c["ev"]))
    return rows


def _render_markdown(result: RunResult) -> str:
    L = []
    L.append("# Scorito WC2026 — Recommended Group-Phase Picks\n")
    L.append(f"_Pool size:_ {result.pool_size} · _Risk:_ {result.risk} · "
             f"_Goal model:_ {'market odds + Elo' if result.used_odds else 'Elo only'}\n")
    L.append("> ⚠️ Confirm in-app before locking: exact **deadline** (11 June 2026, "
             "evening CET) and the topscorer **multiplier/slot count** (4 vs 6).\n")
    L.append(f"\n**Expected group-phase points (model):** {result.expected_group_points:.0f}\n")

    L.append("\n## Group scorelines & standings\n")
    for g in sorted(result.groups):
        gr = result.groups[g]
        L.append(f"\n### Group {g}\n")
        L.append("| Match | Pick | EV |")
        L.append("|---|---|---|")
        for (a, b), s in zip(gr.matches, gr.scorelines):
            L.append(f"| {a} vs {b} | **{s.home}-{s.away}** | {s.ev:.1f} |")
        standing = " → ".join(f"{i}. {t}" for i, t in enumerate(gr.predicted_standing, 1))
        L.append(f"\nPredicted standing: **{standing}**  ")
        L.append(f"\n_Expected: {gr.match_pts:.0f} (matches) + {gr.stand_pts:.0f} "
                 f"(standings) = **{gr.total:.0f}** pts_\n")

    L.append("\n## Champion (250 pts)\n")
    L.append("| Team | P(win) | EV | Est. pool share | Leverage |")
    L.append("|---|---|---|---|---|")
    for r in result.champion[:5]:
        L.append(f"| {r.team} | {r.p_win:.1%} | {r.ev_points:.0f} | {r.est_share:.0%} | {r.leverage:.4f} |")
    rec = result.champion[0]
    runner = result.champion[1]
    L.append(f"\n**Recommendation: {rec.team}** (best pool-adjusted leverage). "
             f"{runner.team} is essentially tied — pick {runner.team} if you want more "
             f"differentiation from the field.\n")

    L.append("\n## Topscorers (pick 6)\n")
    L.append("The 4:2:1 defender:mid:attacker multiplier is the edge — note the "
             "high-value defenders/penalty-takers.\n")
    L.append("| Player | Team | Pos | Pen | EV |")
    L.append("|---|---|---|---|---|")
    for c in result.topscorers:
        L.append(f"| {c['name']} | {c['team']} | {c['position']} | "
                 f"{'✓' if c.get('pen_taker') else ''} | {c['ev']:.2f} |")
    L.append("\n_Topscorer g90/start estimates are editable in "
             "`scorito/data/topscorer_candidates.py` — adjust for late squad news._\n")
    return "\n".join(L)


def write_report(result: RunResult, out_dir: str = "out"):
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, "report.md")
    csv_path = os.path.join(out_dir, "picks.csv")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(_render_markdown(result))
    rows = build_csv_rows(result.groups, result.champion, result.topscorers)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["type", "group", "item", "detail", "value"])
        w.writeheader()
        w.writerows(rows)
    return md_path, csv_path
