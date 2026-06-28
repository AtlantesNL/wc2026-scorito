import pytest

from scorito.model import bracket as bk


def test_parse_refs():
    assert bk._parse_ref("1A") == bk.GroupPos(1, "A")
    assert bk._parse_ref("2B") == bk.GroupPos(2, "B")
    assert bk._parse_ref("3A/B/C/D/F") == bk.ThirdSlot(frozenset("ABCDF"))
    assert bk._parse_ref("W74") == bk.WinnerOf(74)
    assert bk._parse_ref("L101") == bk.LoserOf(101)


def test_parse_ref_rejects_garbage():
    with pytest.raises(ValueError):
        bk._parse_ref("XYZ")


def test_load_bracket_real_fixture():
    b = bk.load_bracket("data/worldcup2026_fixtures.json")
    assert len(b) == 32                       # 16+8+4+2+1+1
    rounds = {m.round for m in b}
    assert "Round of 32" in rounds and "Final" in rounds
    r32 = [m for m in b if m.round == "Round of 32"]
    assert len(r32) == 16
    thirds = [r for m in b for r in (m.team1, m.team2) if isinstance(r, bk.ThirdSlot)]
    assert len(thirds) == 8                   # eight third-place slots in R32
    final = [m for m in b if m.round == "Final"][0]
    assert isinstance(final.team1, bk.WinnerOf) and isinstance(final.team2, bk.WinnerOf)


def test_qualify_thirds_takes_best_eight_by_pts_gd_gf():
    thirds = [dict(team=f"T{i}", group="ABCDEFGHIJKL"[i],
                   pts=i, gd=0, gf=0) for i in range(12)]
    q = bk.qualify_thirds(thirds)
    assert len(q) == 8
    assert {t["team"] for t in q} == {f"T{i}" for i in range(4, 12)}  # top 8 by pts


def test_assign_thirds_respects_allowed_groups():
    qualified = [dict(team="TA", group="A", pts=5, gd=1, gf=2),
                 dict(team="TC", group="C", pts=4, gd=0, gf=1)]
    slots = [frozenset("AB"), frozenset("CD")]
    assigned = bk.assign_thirds(qualified, slots)
    assert assigned[0]["group"] == "A"   # slot 0 ({A,B}) -> the group-A team
    assert assigned[1]["group"] == "C"   # slot 1 ({C,D}) -> the group-C team
