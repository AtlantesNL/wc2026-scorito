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


def test_types_construct():
    t = Team(name="Spain", code="ESP", group="H", elo=2100.0, confederation="UEFA")
    mt = Match(team1="Spain", team2="Uruguay", group="H", matchday=1, date="2026-06-15")
    s = Scoreline(home=1, away=0, ev=22.6)
    assert t.elo == 2100.0 and mt.group == "H" and s.toto() == "H"
    assert Scoreline(0, 0).toto() == "D" and Scoreline(0, 2).toto() == "A"


def test_scoreline_leverage_constants():
    assert 0 < config.DRAW_AVERSION < 1
    assert config.SCORELINE_LEVERAGE_GAMMA["max_ev"] == 0.0
    assert config.SCORELINE_LEVERAGE_GAMMA["aggressive"] > config.SCORELINE_LEVERAGE_GAMMA["balanced"] > 0


def test_atgs_constants():
    assert config.ATGS_MARGIN > 1.0
    assert "eu" in config.ATGS_REGIONS


def test_field_sharpness_realistic():
    assert 1.0 <= config.FIELD_SHARPNESS < 2.0   # amateur dispersion, not syndicate-chalk (2.0+)
