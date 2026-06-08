"""Current national-team Elo ratings from eloratings.net.

eloratings.net is a JS app; the data it renders is served as TSV:
- ``en.teams.tsv``: ``code<TAB>primary_name<TAB>alias...`` (244 teams)
- ``World.tsv``: per team, col 2 = code, col 3 = current rating (+ 28 more cols)

We parse both into ``{name: rating}`` and cache to disk. Ratings move slowly, so
a cached snapshot is fine for a tournament. 45/48 WC-2026 team names match
eloratings exactly; the 3 exceptions are mapped below.
"""
import json
import os
import warnings

import requests

WORLD_TSV = "https://www.eloratings.net/World.tsv"
TEAMS_TSV = "https://www.eloratings.net/en.teams.tsv"

# openfootball name -> eloratings primary name (only the mismatches)
OPENFOOTBALL_TO_ELO = {
    "USA": "United States",
    "Czech Republic": "Czechia",
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
}


def parse_teams_tsv(text: str) -> dict[str, str]:
    """``code -> primary english name``."""
    out = {}
    for line in text.splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[0]:
            out[p[0]] = p[1]
    return out


def parse_world_tsv(text: str, code2name: dict[str, str]) -> dict[str, float]:
    """``name -> current rating`` (World.tsv col 2 = code, col 3 = rating)."""
    out = {}
    for line in text.splitlines():
        p = line.split("\t")
        if len(p) >= 4 and p[2] in code2name:
            try:
                out[code2name[p[2]]] = float(p[3])
            except ValueError:
                pass
    return out


def normalize_name(name: str) -> str:
    return OPENFOOTBALL_TO_ELO.get(name, name)


def _fetch_ratings() -> dict[str, float]:
    code2name = parse_teams_tsv(requests.get(TEAMS_TSV, timeout=30).text)
    return parse_world_tsv(requests.get(WORLD_TSV, timeout=30).text, code2name)


def get_elo(teams, cache_path: str = "data/cache/elo.json", refresh: bool = False) -> dict[str, float]:
    """Return ``{openfootball_team_name: elo}`` for the requested teams.

    Loads from cache if present (unless ``refresh``), else fetches and caches.
    Unknown teams default to 1500 with a warning.
    """
    ratings = None
    if os.path.exists(cache_path) and not refresh:
        with open(cache_path, encoding="utf-8") as f:
            ratings = json.load(f)
    if ratings is None:
        ratings = _fetch_ratings()
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(ratings, f, ensure_ascii=False)

    out, missing = {}, []
    for t in teams:
        r = ratings.get(normalize_name(t))
        if r is None:
            missing.append(t)
            r = 1500.0
        out[t] = float(r)
    if missing:
        warnings.warn(f"No Elo for {missing}; defaulted to 1500.")
    return out
