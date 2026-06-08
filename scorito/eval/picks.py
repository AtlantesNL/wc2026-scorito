"""Parse out/picks.csv (schema from scorito.report.build_csv_rows) into structured picks."""
import csv
import re

_TS = re.compile(r"^(?P<name>.+?)\s*\((?P<team>.+),\s*(?P<pos>GK|DEF|MID|ATT)\)\s*$")


def load_picks(path):
    scorelines, standings, champion, topscorers = {}, {}, None, []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = row["type"]
            if t == "match":
                a, b = row["item"].split(" vs ")
                h, w = row["detail"].split("-")
                scorelines[(a.strip(), b.strip())] = (int(h), int(w))
            elif t == "standing":
                team = row["item"].split(". ", 1)[1]
                standings.setdefault(row["group"], []).append(team)
            elif t == "champion":
                champion = row["item"].strip()
            elif t == "topscorer":
                m = _TS.match(row["item"])
                if m:
                    topscorers.append(dict(name=m["name"].strip(),
                                           team=m["team"].strip(), position=m["pos"]))
    return dict(scorelines=scorelines, standings=standings,
                champion=champion, topscorers=topscorers)
