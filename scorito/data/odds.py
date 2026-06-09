"""The Odds API client for FIFA World Cup 2026.

Pulls ``soccer_fifa_world_cup`` h2h (+ totals) odds and reduces each match to a
consensus (median across bookmakers) 1X2 price plus an over/under line. Free tier
is 500 requests/month; one call returns every listed match. Team names are mapped
to the openfootball spelling used everywhere else.
"""
import statistics
import unicodedata

import requests

from scorito import config

ODDS_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds"

# The Odds API uses full English names; map the few that differ from openfootball.
# Extend this once you see the real feed (names occasionally vary by provider).
ODDS_TO_OPENFOOTBALL = {
    "United States": "USA",
    "Czechia": "Czech Republic",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
}


def _ofb(name: str) -> str:
    return ODDS_TO_OPENFOOTBALL.get(name, name)


def fetch_odds(api_key: str, regions: str = "eu", markets: str = "h2h,totals"):
    r = requests.get(
        ODDS_URL,
        params=dict(regions=regions, markets=markets, oddsFormat="decimal", apiKey=api_key),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def parse_odds(data):
    """``{(home, away): {"odds": [h, d, a], "total_line": x|None}}`` (median across books)."""
    out = {}
    for ev in data:
        home_raw, away_raw = ev["home_team"], ev["away_team"]
        h, d, a, totals = [], [], [], []
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk["key"] == "h2h":
                    px = {o["name"]: o["price"] for o in mk["outcomes"]}
                    if home_raw in px:
                        h.append(px[home_raw])
                    if away_raw in px:
                        a.append(px[away_raw])
                    if "Draw" in px:
                        d.append(px["Draw"])
                elif mk["key"] == "totals":
                    pts = [o["point"] for o in mk["outcomes"] if o.get("point") is not None]
                    if pts:
                        totals.append(statistics.median(pts))
        if not (h and d and a):
            continue  # incomplete 1X2 — skip, Elo will cover this match
        out[(_ofb(home_raw), _ofb(away_raw))] = {
            "odds": [statistics.median(h), statistics.median(d), statistics.median(a)],
            "total_line": statistics.median(totals) if totals else None,
        }
    return out


EVENTS_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events"
EVENT_ODDS_URL = "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/events/{eid}/odds"

# Our-candidate-name -> the name The Odds API lists, for the few that don't normalize-match.
# Populate during the real run once the feed's spellings are known.
ATGS_PLAYER_ALIASES = {}


def _norm(name: str) -> str:
    """Casefold + strip accents/punctuation for player-name matching across sources."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def fetch_atgs(api_key, regions=None):
    """List WC events, then pull player_goal_scorer_anytime per event. Returns a list of per-event
    /odds JSON responses (cache it; replay via --atgs-file). Failed events are skipped."""
    regions = regions or config.ATGS_REGIONS
    ev = requests.get(EVENTS_URL, params=dict(apiKey=api_key), timeout=30)
    ev.raise_for_status()
    out = []
    for e in ev.json():
        try:
            r = requests.get(
                EVENT_ODDS_URL.format(eid=e["id"]),
                params=dict(regions=regions, markets="player_goal_scorer_anytime",
                            oddsFormat="decimal", apiKey=api_key),
                timeout=30,
            )
            r.raise_for_status()
            out.append(r.json())
        except requests.RequestException:
            continue
    return out


def parse_atgs(raw):
    """``raw``: list of per-event /odds responses. -> ``{(home_ofb, away_ofb): {norm_player: median_price}}``."""
    out = {}
    for ev in raw:
        key = (_ofb(ev["home_team"]), _ofb(ev["away_team"]))
        prices = {}
        for bk in ev.get("bookmakers", []):
            for mk in bk.get("markets", []):
                if mk.get("key") != "player_goal_scorer_anytime":
                    continue
                for o in mk.get("outcomes", []):
                    if o.get("name") in ("No", "Under"):       # negative leg
                        continue
                    player = o.get("description") or o.get("name", "")
                    if player in ("", "Yes", "No", "Over", "Under"):
                        continue
                    prices.setdefault(_norm(player), []).append(o["price"])
        if prices:
            out[key] = {p: statistics.median(v) for p, v in prices.items()}
    return out
