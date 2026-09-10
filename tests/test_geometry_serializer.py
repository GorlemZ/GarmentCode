from copy import deepcopy

import pytest
import yaml

from pygarment.serialization.geometry import GeometryInputError, serialize_geometry
from pygarment.use_cases.tee import TeeRequest, generate_tee


def _assembly():
    with open("assets/bodies/mean_all.yaml", encoding="utf-8") as body_file:
        body = yaml.safe_load(body_file)["body"]
    with open("assets/design_params/t-shirt.yaml", encoding="utf-8") as design_file:
        design = yaml.safe_load(design_file)["design"]
    return generate_tee(TeeRequest.from_mapping({"body": body, "design": design}))


def test_serialize_geometry_returns_versioned_typed_document():
    document = serialize_geometry(_assembly())

    assert document.version == "geometry.v1"
    assert document.units == "cm"
    assert document.pieces
    assert document.stitches
    assert document.bounds.minimum.x < document.bounds.maximum.x
    assert document.bounds.minimum.y < document.bounds.maximum.y


def test_serialized_geometry_has_explicit_public_shape():
    result = serialize_geometry(_assembly()).to_mapping()

    assert set(result) == {"version", "units", "pieces", "stitches", "bounds", "diagnostics"}
    assert set(result["pieces"][0]) == {
        "name",
        "label",
        "vertices",
        "edges",
        "translation",
        "rotation",
    }
    assert set(result["pieces"][0]["vertices"][0]) == {"x", "y"}
    assert set(result["pieces"][0]["edges"][0]) >= {"start", "end"}
    assert "pattern" not in result
    assert "__dict__" not in result


def test_geometry_serialization_is_deterministic_and_does_not_mutate_assembly():
    assembly = _assembly()
    original = deepcopy(assembly.pattern)

    first = serialize_geometry(assembly).to_mapping()
    second = serialize_geometry(assembly).to_mapping()

    assert first == second
    assert assembly.pattern == original


def test_serialize_geometry_rejects_an_invalid_assembly():
    with pytest.raises(GeometryInputError, match="assembly.pattern"):
        serialize_geometry(object())


def test_serialize_geometry_rejects_stitches_to_unknown_edges():
    assembly = _assembly()
    assembly.pattern["stitches"][0][0]["panel"] = "missing-panel"

    with pytest.raises(GeometryInputError, match="stitch reference"):
        serialize_geometry(assembly)
