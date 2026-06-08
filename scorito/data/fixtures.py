"""Load World Cup 2026 fixtures from openfootball/worldcup.json.

Schema (verified 2026-06-08): top-level ``{"name", "matches": [...]}`` where each
match has ``round, date, time, team1, team2, group, ground``. Group-stage matches
carry ``group: "Group A".."Group L"``; the 32 knockout matches have no ``group``
(and placeholder team names like ``"W101"``), so we skip them for the group phase.
"""
import json

import requests

from scorito.types import Match

WORLDCUP_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
)


def _matchday(round_str: str) -> int:
    digits = "".join(ch for ch in round_str if ch.isdigit())
    return int(digits) if digits else 1


def load_fixtures(path_or_url: str = WORLDCUP_URL):
    """Return a list of group-stage ``Match`` objects (knockouts excluded)."""
    if str(path_or_url).startswith("http"):
        data = requests.get(path_or_url, timeout=30).json()
    else:
        with open(path_or_url, encoding="utf-8") as f:
            data = json.load(f)

    matches = []
    for m in data["matches"]:
        grp = m.get("group")
        if not grp:
            continue  # knockout stage
        matches.append(
            Match(
                team1=m["team1"],
                team2=m["team2"],
                group=grp.replace("Group ", "").strip(),
                matchday=_matchday(m.get("round", "")),
                date=m.get("date", ""),
            )
        )
    return matches


def group_teams(matches):
    """Map ``group -> [team names]`` in first-seen order."""
    out: dict[str, list[str]] = {}
    for m in matches:
        teams = out.setdefault(m.group, [])
        for t in (m.team1, m.team2):
            if t not in teams:
                teams.append(t)
    return out
