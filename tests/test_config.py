from scorito import config
from scorito.types import Team, Match, Scoreline


def test_scoring_constants():
    assert config.PTS_EXACT == 45
    assert config.PTS_TOTO == 30
    assert config.PTS_POSITION == 25
    assert config.CHAMPION_BONUS == 250
    assert config.TOPSCORER_SLOTS == 6


def test_topscorer_points_confirmed():
    m = config.TOPSCORER_MULT
    # Confirmed in-app (group phase): ATT 8 / MID 16 / DEF 32 / GK 32
    assert m["ATT"] == 8 and m["MID"] == 16 and m["DEF"] == 32 and m["GK"] == 32
    # ratio DEF/GK : MID : ATT = 4 : 2 : 1 drives selection
    assert m["DEF"] / m["ATT"] == 4 and m["MID"] / m["ATT"] == 2


def test_scoreline_toto_weight():
    w = config.scoreline_toto_weight
    # max_ev is always pure EV regardless of pool size
    assert w("max_ev", 40) == 1.0 and w("max_ev", 1000) == 1.0
    # tiny pool -> no tilt even for aggressive
    assert w("aggressive", 10) == 1.0
    # bigger pool -> stronger tilt (lower weight); capped, never absurd
    small, big = w("aggressive", 20), w("aggressive", 500)
    assert 0.9 < small <= 1.0
    assert 0.1 <= big < small
    # aggressive tilts more than balanced at the same (large) pool
    assert w("aggressive", 500) < w("balanced", 500) < 1.0


def test_types_construct():
    t = Team(name="Spain", code="ESP", group="H", elo=2100.0, confederation="UEFA")
    mt = Match(team1="Spain", team2="Uruguay", group="H", matchday=1, date="2026-06-15")
    s = Scoreline(home=1, away=0, ev=22.6)
    assert t.elo == 2100.0 and mt.group == "H" and s.toto() == "H"
    assert Scoreline(0, 0).toto() == "D" and Scoreline(0, 2).toto() == "A"
