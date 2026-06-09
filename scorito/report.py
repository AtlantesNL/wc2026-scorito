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
    advance: dict = field(default_factory=dict)   # team -> {"r16","qf","sf","final","win"}
    pool_win: dict = field(default_factory=dict)  # team -> P(our entry finishes 1st in the pool)

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
    n_draws = sum(1 for gr in result.groups.values() for s in gr.scorelines if s.home == s.away)
    n_sl = sum(len(gr.scorelines) for gr in result.groups.values())
    L.append(f"_Scorelines:_ pool-leverage-adjusted (draw-aware); "
             f"{n_draws}/{n_sl} predicted draws\n")
    L.append("> ⚠️ Confirm the exact **deadline** in-app (11 June 2026, evening CET). "
             "Topscorer scoring confirmed: 6 picks; 8/16/32/32 pts per goal "
             "(Aanvaller/Middenvelder/Verdediger/Keeper).\n")
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
    L.append("| Team | P(win) | Win-pool | EV | Share | Lev | R16 | QF | SF | Final |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in result.champion[:5]:
        a = result.advance.get(r.team, {})
        wp = result.pool_win.get(r.team)
        wp_s = f"{wp:.1%}" if wp is not None else "–"
        L.append(f"| {r.team} | {r.p_win:.1%} | {wp_s} | {r.ev_points:.0f} | {r.est_share:.0%} | "
                 f"{r.leverage:.4f} | {a.get('r16', 0):.0%} | {a.get('qf', 0):.0%} | "
                 f"{a.get('sf', 0):.0%} | {a.get('final', 0):.0%} |")
    rec = result.champion[0]
    wp = result.pool_win.get(rec.team)
    if wp is not None:
        sims = result.meta.get("pool_win_sims", 0) or 1
        top = max(result.pool_win.values())
        se = (max(top * (1.0 - top), 1e-9) / sims) ** 0.5          # Monte-Carlo std error
        cluster = sorted((t for t, p in result.pool_win.items() if p >= top - 2 * se),
                         key=lambda t: -result.pool_win[t])
        names = ", ".join(f"{t} {result.pool_win[t]:.1%}" for t in cluster[:5])
        L.append(f"\n**Champion — pick from the leverage cluster** (statistically tied within "
                 f"~2 Monte-Carlo std-errors, ±{se:.1%}): {names}. Default: **{rec.team}**. These "
                 f"all out-leverage the over-owned favourites; choose the one you most believe "
                 f"will lift the trophy — and avoid host nations (USA/Mexico/Canada), which "
                 f"amateurs over-pick.\n")
    else:
        runner = result.champion[1]
        L.append(f"\n**Recommendation: {rec.team}** (pool-adjusted leverage); "
                 f"{runner.team} close.\n")

    L.append("\n## Topscorers (pick 6)\n")
    L.append("Per goal: ATT 8 / MID 16 / DEF 32 / GK 32 — the 4:2:1 edge means a "
             "defender's goal is worth four of a striker's. EV below is expected "
             "group-phase points.\n")
    if result.meta.get("ts_pool_win") is not None:
        L.append(f"_Engine-selected to maximize P(finishing 1st)_ vs a fame-biased field "
                 f"(over-owns famous attackers); entry pool-win {result.meta['ts_pool_win']:.1%}.\n")
    n_mkt = sum(1 for c in result.topscorers if c.get("goals_src") in ("market", "blend"))
    if n_mkt:
        L.append(f"_📈 = anytime-goalscorer market rate ({n_mkt}/{len(result.topscorers)}); "
                 f"✍️ = hand-estimated g90._\n")
    L.append("| Player | Team | Pos | Pen | Src | EV |")
    L.append("|---|---|---|---|---|---|")
    for c in result.topscorers:
        src = "📈" if c.get("goals_src") in ("market", "blend") else "✍️"
        L.append(f"| {c['name']} | {c['team']} | {c['position']} | "
                 f"{'✓' if c.get('pen_taker') else ''} | {src} | {c['ev']:.2f} |")
    L.append("\n_Picks are auto-validated against the confirmed 2026 squads; g90/start "
             "estimates are editable in `scorito/data/topscorer_candidates.py`._\n")
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
