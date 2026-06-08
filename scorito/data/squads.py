"""Validate topscorer candidates against the confirmed 2026 World Cup squads.

Squads were locked on 2 June 2026, so a snapshot is the correct model (like the
Elo/Opta data) — no fragile live scraping. ``squads_2026.json`` maps each team to
the set of ASCII-folded surname tokens parsed from FIFA's official squad-list PDF
(anchored on each player's date of birth, which sits right after the name-on-shirt).

Matching is deliberately lenient toward KEEPING a player: a candidate is in the
squad if ANY token of his name (len >= 4, folded) appears in the team's set. False
keeps (a phantom slips through) are tolerable; false drops (losing a real star to a
spelling mismatch) are not. If we have no data for a team, the candidate is kept.
"""
import json
import os
import re
import unicodedata

_DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "squads_2026.json")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if c.isascii() and c.isalpha()).upper()


def name_tokens(name: str):
    """Folded tokens of a full name, length >= 4 (drops short common bits)."""
    out = []
    for part in name.split():
        for piece in re.split(r"[-']", part):
            t = fold(piece)
            if len(t) >= 4:
                out.append(t)
    return out


def load_squads(path: str = _DEFAULT_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def in_squad(player_name: str, team: str, squads: dict) -> bool:
    roster = squads.get(team)
    if not roster:
        return True  # no data for this team -> cannot validate -> keep (safe)
    rset = set(roster)
    return any(t in rset for t in name_tokens(player_name))


def validate_candidates(candidates, squads):
    """Split candidates into (kept, dropped) by squad membership."""
    kept, dropped = [], []
    for c in candidates:
        (kept if in_squad(c["name"], c["team"], squads) else dropped).append(c)
    return kept, dropped
