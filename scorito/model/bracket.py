"""Parse the openfootball knockout tree into typed references + third-place matching.

Pure structure/assignment logic. Token grammar in the fixtures file:
  "1A"/"2B"    -> GroupPos(pos, group)
  "3A/B/C/D/F" -> ThirdSlot(allowed groups)      (eight such slots in the Round of 32)
  "W74"/"L101" -> WinnerOf / LoserOf match number
The Final ("W101 vs W102") and third-place playoff ("L101 vs L102") have num=None in the
source; we give them synthetic numbers > all real ones so they sort last.
"""
import json
import re
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class GroupPos:
    pos: int
    group: str


@dataclass(frozen=True)
class ThirdSlot:
    allowed: frozenset


@dataclass(frozen=True)
class WinnerOf:
    num: int


@dataclass(frozen=True)
class LoserOf:
    num: int


@dataclass
class KOMatch:
    num: int
    round: str
    team1: object
    team2: object


def _parse_ref(tok):
    tok = str(tok).strip()
    m = re.fullmatch(r"([12])([A-L])", tok)
    if m:
        return GroupPos(int(m.group(1)), m.group(2))
    m = re.fullmatch(r"3([A-L](?:/[A-L])*)", tok)
    if m:
        return ThirdSlot(frozenset(m.group(1).split("/")))
    m = re.fullmatch(r"W(\d+)", tok)
    if m:
        return WinnerOf(int(m.group(1)))
    m = re.fullmatch(r"L(\d+)", tok)
    if m:
        return LoserOf(int(m.group(1)))
    raise ValueError(f"Unparseable bracket token: {tok!r}")


def load_bracket(fixtures_src):
    """Return the 32 knockout matches as KOMatch nodes, ordered by num."""
    if str(fixtures_src).startswith("http"):
        data = requests.get(fixtures_src, timeout=30).json()
    else:
        with open(fixtures_src, encoding="utf-8") as f:
            data = json.load(f)
    ko = [m for m in data["matches"] if not m.get("group")]
    out, synth = [], 10_000
    for m in ko:
        num = m.get("num")
        if num is None:
            num = synth
            synth += 1
        out.append(KOMatch(num=num, round=m["round"],
                           team1=_parse_ref(m["team1"]), team2=_parse_ref(m["team2"])))
    out.sort(key=lambda x: x.num)
    return out
