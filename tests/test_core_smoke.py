def test_tshirt_core_smoke(tshirt_garment, tshirt_pattern):
    assert tshirt_pattern.name == "t-shirt"
    assert len(tshirt_pattern.pattern["panels"]) == 8
    assert len(tshirt_pattern.pattern["stitches"]) == 16
    assert tshirt_garment.is_self_intersecting() is False
