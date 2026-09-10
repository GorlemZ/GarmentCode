from copy import deepcopy

import pytest
import yaml

from pygarment.use_cases.tee import TeeInputError, TeeRequest, generate_tee


def _input():
    with open("assets/bodies/mean_all.yaml", encoding="utf-8") as body_file:
        body = yaml.safe_load(body_file)["body"]
    with open("assets/design_params/t-shirt.yaml", encoding="utf-8") as design_file:
        design = yaml.safe_load(design_file)["design"]
    return {"body": body, "design": design}


def test_generate_tee_returns_assembly():
    result = generate_tee(TeeRequest.from_mapping(_input()))

    assert result.name == "t-shirt"
    assert result.pattern["panels"]
    assert result.pattern["stitches"]


def test_generate_tee_does_not_mutate_input():
    request = _input()
    original = deepcopy(request)

    generate_tee(TeeRequest.from_mapping(request))

    assert request == original


@pytest.mark.parametrize("payload", [{}, {"body": {}}, {"body": {}, "design": {}}])
def test_generate_tee_rejects_incomplete_input(payload):
    with pytest.raises(TeeInputError):
        TeeRequest.from_mapping(payload)


def test_generate_tee_rejects_non_mapping_input():
    with pytest.raises(TeeInputError):
        TeeRequest.from_mapping([])


def test_generate_tee_rejects_incomplete_body_or_design():
    payload = _input()

    del payload["body"]["height"]
    with pytest.raises(TeeInputError, match="body is missing"):
        TeeRequest.from_mapping(payload)

    payload = _input()
    del payload["design"]["sleeve"]
    with pytest.raises(TeeInputError, match="design is missing"):
        TeeRequest.from_mapping(payload)


@pytest.mark.parametrize("field", ["height", "bust", "shoulder_w"])
def test_tee_request_rejects_null_required_body_fields(field):
    payload = _input()
    payload["body"][field] = None

    with pytest.raises(TeeInputError, match=f"body.{field} must be a number"):
        TeeRequest.from_mapping(payload)


def test_generate_tee_rejects_unvalidated_mapping():
    with pytest.raises(TypeError, match="TeeRequest"):
        generate_tee(_input())
