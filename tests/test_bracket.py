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
    b = bk.load_bracket("data/cache/worldcup2026.json")
    assert len(b) == 32                       # 16+8+4+2+1+1
    rounds = {m.round for m in b}
    assert "Round of 32" in rounds and "Final" in rounds
    r32 = [m for m in b if m.round == "Round of 32"]
    assert len(r32) == 16
    thirds = [r for m in b for r in (m.team1, m.team2) if isinstance(r, bk.ThirdSlot)]
    assert len(thirds) == 8                   # eight third-place slots in R32
    final = [m for m in b if m.round == "Final"][0]
    assert isinstance(final.team1, bk.WinnerOf) and isinstance(final.team2, bk.WinnerOf)
