import copy
import json

import numpy as np
import pytest

from pygarment.pattern.core import BasicPattern


pytestmark = pytest.mark.core


def _basic_pattern_copy(source_pattern):
    pattern = BasicPattern()
    pattern.name = source_pattern.name
    pattern.spec = copy.deepcopy(source_pattern.spec)
    pattern.pattern = pattern.spec["pattern"]
    pattern.properties = pattern.spec["properties"]
    return pattern


def test_json_round_trip_preserves_panels_stitches_and_properties(tshirt_pattern, tmp_path):
    pattern = _basic_pattern_copy(tshirt_pattern)

    output_dir = pattern.serialize(tmp_path, to_subfolder=False)
    spec_file = output_dir / f"{pattern.name}_specification.json"

    reloaded = BasicPattern(str(spec_file))

    assert reloaded.name == pattern.name
    assert reloaded.panel_order() == pattern.panel_order()
    assert len(reloaded.pattern["panels"]) == len(pattern.pattern["panels"])
    assert len(reloaded.pattern["stitches"]) == len(pattern.pattern["stitches"])
    assert reloaded.properties["units_in_meter"] == 100


def test_serialize_writes_to_explicit_directory_without_cwd_dependency(tshirt_pattern, tmp_path, monkeypatch):
    pattern = _basic_pattern_copy(tshirt_pattern)
    outside_cwd = tmp_path / "outside"
    target_dir = tmp_path / "target"
    outside_cwd.mkdir()
    target_dir.mkdir()
    monkeypatch.chdir(outside_cwd)

    output_dir = pattern.serialize(target_dir, to_subfolder=False)

    assert output_dir == target_dir
    assert (target_dir / f"{pattern.name}_specification.json").exists()
    assert not (outside_cwd / f"{pattern.name}_specification.json").exists()


def test_reloaded_pattern_normalizes_units_to_centimeters(tmp_path):
    spec = {
        "pattern": {
            "panels": {
                "square": {
                    "translation": [1, 2, 3],
                    "rotation": [0, 0, 0],
                    "vertices": [[0, 0], [1, 0], [1, 1], [0, 1]],
                    "edges": [
                        {"endpoints": [0, 1]},
                        {"endpoints": [1, 2]},
                        {"endpoints": [2, 3]},
                        {"endpoints": [3, 0]},
                    ],
                }
            },
            "stitches": [],
        },
        "parameters": {},
        "parameter_order": [],
        "properties": {
            "curvature_coords": "relative",
            "normalize_panel_translation": False,
            "normalized_edge_loops": True,
            "units_in_meter": 1,
        },
    }
    spec_file = tmp_path / "square_specification.json"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")

    pattern = BasicPattern(str(spec_file))

    assert pattern.properties["units_in_meter"] == 100
    assert pattern.pattern["panels"]["square"]["translation"] == pytest.approx([100, 200, 300])
    vertices = np.asarray(pattern.pattern["panels"]["square"]["vertices"])
    assert vertices == pytest.approx(
        np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
    )
