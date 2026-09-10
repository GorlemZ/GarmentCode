"""Stateless T-shirt generation use case."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, fields
from math import isfinite
from numbers import Real

from pygarment.programs.body_params import BodyParameters
from pygarment.programs.meta_garment import MetaGarment


class TeeInputError(ValueError):
    """Raised when a T-shirt request does not contain valid input."""


_REQUIRED_DESIGN_SECTIONS = {"meta", "waistband", "shirt", "collar", "sleeve", "left"}


@dataclass(frozen=True)
class BodyMeasurements:
    """Validated, non-null body measurements required by the T-shirt program."""

    arm_length: float
    arm_pose_angle: float
    armscye_depth: float
    back_width: float
    bum_points: float
    bust: float
    bust_line: float
    bust_points: float
    crotch_hip_diff: float
    head_l: float
    height: float
    hip_back_width: float
    hip_inclination: float
    hips: float
    hips_line: float
    leg_circ: float
    neck_w: float
    shoulder_incl: float
    shoulder_w: float
    underbust: float
    vert_bust_line: float
    waist: float
    waist_back_width: float
    waist_line: float
    waist_over_bust_line: float
    wrist: float

    @classmethod
    def from_mapping(cls, body: object) -> "BodyMeasurements":
        if not isinstance(body, Mapping):
            raise TeeInputError("request.body must be a mapping")

        expected = {item.name for item in fields(cls)}
        missing = sorted(expected - body.keys())
        if missing:
            raise TeeInputError(f"request.body is missing fields: {', '.join(missing)}")

        values: dict[str, float] = {}
        for name in expected:
            value = body[name]
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
                raise TeeInputError(f"request.body.{name} must be a number")
            values[name] = float(value)
        return cls(**values)

    def as_mapping(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class TeeRequest:
    """Validated input accepted by the T-shirt generation use case."""

    body: BodyMeasurements
    design: Mapping[str, object]

    @classmethod
    def from_mapping(cls, request: object) -> "TeeRequest":
        if not isinstance(request, Mapping):
            raise TeeInputError("request must be a mapping")

        body = BodyMeasurements.from_mapping(request.get("body"))
        design = request.get("design")
        if not isinstance(design, Mapping):
            raise TeeInputError("request.design must be a mapping")

        missing_sections = sorted(_REQUIRED_DESIGN_SECTIONS - design.keys())
        if missing_sections:
            raise TeeInputError(
                f"request.design is missing sections: {', '.join(missing_sections)}"
            )

        meta = design.get("meta")
        if not isinstance(meta, Mapping):
            raise TeeInputError("request.design.meta must be a mapping")
        for key in ("upper", "bottom", "wb"):
            value = meta.get(key)
            if not isinstance(value, Mapping) or "v" not in value:
                raise TeeInputError(f"request.design.meta.{key}.v is required")

        return cls(body=body, design=deepcopy(dict(design)))



def generate_tee(request: TeeRequest):
    """Generate a T-shirt assembly from a validated request DTO."""
    if not isinstance(request, TeeRequest):
        raise TypeError("request must be a TeeRequest")

    body_params = BodyParameters()
    body_params.load_from_dict(request.body.as_mapping())
    garment = MetaGarment("t-shirt", body_params, deepcopy(dict(request.design)))
    garment.assert_non_empty()
    garment.assert_skirt_waistband()
    garment.assert_total_length()
    return garment.assembly()


__all__ = [
    "BodyMeasurements",
    "TeeInputError",
    "TeeRequest",
    "generate_tee",
]
