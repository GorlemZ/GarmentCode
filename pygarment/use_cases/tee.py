"""Stateless T-shirt generation use case."""

from collections.abc import Mapping
from copy import deepcopy

from pygarment.programs.body_params import BodyParameters
from pygarment.programs.meta_garment import MetaGarment


class TeeInputError(ValueError):
    """Raised when a T-shirt request does not contain the full input shape."""


_REQUIRED_BODY_FIELDS = {
    "arm_length",
    "arm_pose_angle",
    "armscye_depth",
    "back_width",
    "bust",
    "bust_line",
    "bust_points",
    "head_l",
    "height",
    "hip_inclination",
    "hips",
    "hips_line",
    "neck_w",
    "shoulder_incl",
    "shoulder_w",
    "underbust",
    "vert_bust_line",
    "waist",
    "waist_line",
}
_REQUIRED_DESIGN_SECTIONS = {"meta", "waistband", "shirt", "collar", "sleeve", "left"}


def generate_tee(request: Mapping):
    """Generate a T-shirt assembly from a complete body and design mapping.

    The request is copied before it is passed to the mutable core parameter
    objects. The returned value is the existing ``VisPattern`` assembly; a
    later PR will define the public geometry serializer.
    """
    if not isinstance(request, Mapping):
        raise TeeInputError("request must be a mapping")

    body = request.get("body")
    design = request.get("design")
    if not isinstance(body, Mapping):
        raise TeeInputError("request.body must be a mapping")
    missing_body = sorted(_REQUIRED_BODY_FIELDS - body.keys())
    if missing_body:
        raise TeeInputError(f"request.body is missing fields: {', '.join(missing_body)}")
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
        if not isinstance(meta.get(key), Mapping) or "v" not in meta[key]:
            raise TeeInputError(f"request.design.meta.{key}.v is required")

    body_params = BodyParameters()
    body_params.load_from_dict(deepcopy(dict(body)))
    garment = MetaGarment("t-shirt", body_params, deepcopy(dict(design)))
    garment.assert_non_empty()
    garment.assert_skirt_waistband()
    garment.assert_total_length()
    return garment.assembly()


__all__ = ["TeeInputError", "generate_tee"]