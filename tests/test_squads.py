from scorito.data.squads import (
    fold,
    in_squad,
    load_squads,
    name_tokens,
    validate_candidates,
)


def test_fold_and_name_tokens():
    assert fold("Mbappé") == "MBAPPE"
    assert name_tokens("Trent Alexander-Arnold") == ["TRENT", "ALEXANDER", "ARNOLD"]
    toks = name_tokens("Virgil van Dijk")
    assert "DIJK" in toks and "VAN" not in toks  # 'van' (len 3) dropped


def test_in_squad_present_absent_unknown_team():
    squads = {"England": ["KANE", "BELLINGHAM", "SAKA"]}
    assert in_squad("Harry Kane", "England", squads) is True
    assert in_squad("Cole Palmer", "England", squads) is False
    assert in_squad("Whoever", "Atlantis", squads) is True  # no data -> safe keep


def test_validate_candidates_splits():
    squads = {"England": ["KANE"], "France": ["MBAPPE"]}
    cands = [
        dict(name="Harry Kane", team="England"),
        dict(name="Cole Palmer", team="England"),
        dict(name="Kylian Mbappe", team="France"),
    ]
    kept, dropped = validate_candidates(cands, squads)
    assert [c["name"] for c in kept] == ["Harry Kane", "Kylian Mbappe"]
    assert [c["name"] for c in dropped] == ["Cole Palmer"]


def test_real_squads_data_sanity():
    sq = load_squads()
    assert len(sq) == 48
    assert in_squad("Achraf Hakimi", "Morocco", sq)
    assert in_squad("Pedri", "Spain", sq)
    assert in_squad("Federico Valverde", "Uruguay", sq)
    assert not in_squad("Cole Palmer", "England", sq)
