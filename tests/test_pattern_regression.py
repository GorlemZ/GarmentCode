import json
from pathlib import Path

import numpy as np


FIXTURE = Path(__file__).parent / "fixtures/tshirt_summary.json"


def _rounded_bounds(vertices):
    coordinates = np.asarray(vertices, dtype=float)
    return {
        "min": np.round(coordinates.min(axis=0), 6).tolist(),
        "max": np.round(coordinates.max(axis=0), 6).tolist(),
    }


def _pattern_summary(pattern):
    panels = pattern.pattern["panels"]
    return {
        "name": pattern.name,
        "panel_order": pattern.panel_order(),
        "panels": {
            name: {
                "vertices": len(panel["vertices"]),
                "edges": len(panel["edges"]),
                "bounds": _rounded_bounds(panel["vertices"]),
            }
            for name, panel in sorted(panels.items())
        },
        "stitches": len(pattern.pattern["stitches"]),
        "units_in_meter": pattern.properties["units_in_meter"],
    }


def test_tshirt_pattern_matches_characterization_fixture(tshirt_pattern):
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    actual = _pattern_summary(tshirt_pattern)

    assert actual.keys() == expected.keys()
    assert actual["name"] == expected["name"]
    assert actual["panel_order"] == expected["panel_order"]
    assert actual["stitches"] == expected["stitches"]
    assert actual["units_in_meter"] == expected["units_in_meter"]
    assert actual["panels"].keys() == expected["panels"].keys()

    for name, expected_panel in expected["panels"].items():
        actual_panel = actual["panels"][name]
        assert actual_panel["vertices"] == expected_panel["vertices"]
        assert actual_panel["edges"] == expected_panel["edges"]
        np.testing.assert_allclose(
            actual_panel["bounds"]["min"],
            expected_panel["bounds"]["min"],
            rtol=1e-3,
            atol=5e-2,
        )
        np.testing.assert_allclose(
            actual_panel["bounds"]["max"],
            expected_panel["bounds"]["max"],
            rtol=1e-3,
            atol=5e-2,
        )
