"""Versioned, typed geometry output for web-facing adapters."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import cos, isfinite, radians, sin
from numbers import Real
from typing import Optional, Union


class GeometryInputError(ValueError):
    """Raised when an assembly cannot be converted to geometry."""


@dataclass(frozen=True, init=False)
class Point:
    x: float
    y: float

    @classmethod
    def _create(cls, x: float, y: float) -> "Point":
        instance = object.__new__(cls)
        object.__setattr__(instance, "x", x)
        object.__setattr__(instance, "y", y)
        return instance


@dataclass(frozen=True, init=False)
class Curve:
    type: str
    params: Union[tuple[float, ...], tuple[tuple[float, float], ...]]

    @classmethod
    def _create(
        cls,
        curve_type: str,
        params: Union[tuple[float, ...], tuple[tuple[float, float], ...]],
    ) -> "Curve":
        instance = object.__new__(cls)
        object.__setattr__(instance, "type", curve_type)
        object.__setattr__(instance, "params", params)
        return instance


@dataclass(frozen=True, init=False)
class Edge:
    start: int
    end: int
    label: Optional[str]
    curve: Optional[Curve]

    @classmethod
    def _create(
        cls, start: int, end: int, label: Optional[str], curve: Optional[Curve]
    ) -> "Edge":
        instance = object.__new__(cls)
        object.__setattr__(instance, "start", start)
        object.__setattr__(instance, "end", end)
        object.__setattr__(instance, "label", label)
        object.__setattr__(instance, "curve", curve)
        return instance


@dataclass(frozen=True, init=False)
class Piece:
    name: str
    label: Optional[str]
    vertices: tuple[Point, ...]
    edges: tuple[Edge, ...]
    translation: Point
    rotation: tuple[float, float, float]

    @classmethod
    def _create(
        cls,
        name: str,
        label: Optional[str],
        vertices: tuple[Point, ...],
        edges: tuple[Edge, ...],
        translation: Point,
        rotation: tuple[float, float, float],
    ) -> "Piece":
        instance = object.__new__(cls)
        for field, value in (
            ("name", name),
            ("label", label),
            ("vertices", vertices),
            ("edges", edges),
            ("translation", translation),
            ("rotation", rotation),
        ):
            object.__setattr__(instance, field, value)
        return instance


@dataclass(frozen=True, init=False)
class StitchRef:
    piece: str
    edge: int

    @classmethod
    def _create(cls, piece: str, edge: int) -> "StitchRef":
        instance = object.__new__(cls)
        object.__setattr__(instance, "piece", piece)
        object.__setattr__(instance, "edge", edge)
        return instance


@dataclass(frozen=True, init=False)
class Stitch:
    first: StitchRef
    second: StitchRef
    right_wrong: bool

    @classmethod
    def _create(
        cls, first: StitchRef, second: StitchRef, right_wrong: bool
    ) -> "Stitch":
        instance = object.__new__(cls)
        object.__setattr__(instance, "first", first)
        object.__setattr__(instance, "second", second)
        object.__setattr__(instance, "right_wrong", right_wrong)
        return instance


@dataclass(frozen=True, init=False)
class Bounds:
    minimum: Point
    maximum: Point

    @classmethod
    def _create(cls, minimum: Point, maximum: Point) -> "Bounds":
        instance = object.__new__(cls)
        object.__setattr__(instance, "minimum", minimum)
        object.__setattr__(instance, "maximum", maximum)
        return instance


@dataclass(frozen=True, init=False)
class GeometryDocument:
    version: str
    units: str
    pieces: tuple[Piece, ...]
    stitches: tuple[Stitch, ...]
    bounds: Bounds
    diagnostics: tuple[str, ...]

    @classmethod
    def _create(
        cls,
        pieces: tuple[Piece, ...],
        stitches: tuple[Stitch, ...],
        bounds: Bounds,
    ) -> "GeometryDocument":
        instance = object.__new__(cls)
        for field, value in (
            ("version", "geometry.v1"),
            ("units", "cm"),
            ("pieces", pieces),
            ("stitches", stitches),
            ("bounds", bounds),
            ("diagnostics", ()),
        ):
            object.__setattr__(instance, field, value)
        return instance

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "units": self.units,
            "pieces": [_piece_to_mapping(piece) for piece in self.pieces],
            "stitches": [_stitch_to_mapping(stitch) for stitch in self.stitches],
            "bounds": {
                "minimum": _point_to_mapping(self.bounds.minimum),
                "maximum": _point_to_mapping(self.bounds.maximum),
            },
            "diagnostics": list(self.diagnostics),
        }


def serialize_geometry(assembly: object) -> GeometryDocument:
    """Convert a Tee assembly into the stable geometry DTO."""
    pattern = getattr(assembly, "pattern", None)
    if not isinstance(pattern, Mapping):
        raise GeometryInputError("assembly.pattern must be a mapping")
    panels = pattern.get("panels")
    stitches = pattern.get("stitches")
    if not isinstance(panels, Mapping):
        raise GeometryInputError("assembly.pattern.panels must be a mapping")
    if not isinstance(stitches, list):
        raise GeometryInputError("assembly.pattern.stitches must be a list")

    pieces = tuple(_parse_piece(name, raw_piece) for name, raw_piece in panels.items())
    typed_stitches = tuple(_parse_stitch(raw_stitch) for raw_stitch in stitches)
    _validate_stitch_references(typed_stitches, pieces)
    return GeometryDocument._create(pieces, typed_stitches, _calculate_bounds(pieces))


def _parse_piece(name: object, raw_piece: object) -> Piece:
    if not isinstance(name, str) or not isinstance(raw_piece, Mapping):
        raise GeometryInputError("assembly.pattern.panels contains an invalid piece")
    vertices = raw_piece.get("vertices")
    edges = raw_piece.get("edges")
    translation = raw_piece.get("translation")
    rotation = raw_piece.get("rotation")
    if not isinstance(vertices, list) or not isinstance(edges, list):
        raise GeometryInputError(f"panel {name} must contain vertices and edges")
    return Piece._create(
        name,
        _optional_string(raw_piece.get("label")),
        tuple(_parse_point(point) for point in vertices),
        tuple(_parse_edge(edge, len(vertices)) for edge in edges),
        _parse_translation(translation),
        _parse_rotation(rotation),
    )


def _parse_point(value: object) -> Point:
    if not isinstance(value, list) or len(value) != 2:
        raise GeometryInputError("vertices must contain two coordinates")
    return Point._create(_number(value[0], "vertex.x"), _number(value[1], "vertex.y"))


def _parse_translation(value: object) -> Point:
    if not isinstance(value, list) or len(value) != 3:
        raise GeometryInputError("translation must contain three coordinates")
    return Point._create(_number(value[0], "translation.x"), _number(value[1], "translation.y"))


def _parse_rotation(value: object) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise GeometryInputError("rotation must contain three angles")
    return tuple(_number(item, "rotation") for item in value)  # type: ignore[return-value]


def _parse_edge(value: object, vertex_count: int) -> Edge:
    if not isinstance(value, Mapping):
        raise GeometryInputError("edge must be a mapping")
    endpoints = value.get("endpoints")
    if (
        not isinstance(endpoints, list)
        or len(endpoints) != 2
        or any(not isinstance(item, int) or isinstance(item, bool) for item in endpoints)
        or any(item < 0 or item >= vertex_count for item in endpoints)
    ):
        raise GeometryInputError("edge endpoints must reference panel vertices")
    curve = _parse_curve(value.get("curvature")) if "curvature" in value else None
    return Edge._create(endpoints[0], endpoints[1], _optional_string(value.get("label")), curve)


def _parse_curve(value: object) -> Curve:
    if not isinstance(value, Mapping) or not isinstance(value.get("type"), str):
        raise GeometryInputError("curvature must contain a type")
    curve_type = value["type"]
    params = value.get("params")
    if curve_type == "circle":
        if not isinstance(params, list) or len(params) != 3:
            raise GeometryInputError("circle curvature requires three parameters")
        return Curve._create(curve_type, tuple(_number(item, "circle parameter") for item in params))
    if curve_type == "cubic":
        if (
            not isinstance(params, list)
            or len(params) != 2
            or any(not isinstance(item, list) or len(item) != 2 for item in params)
        ):
            raise GeometryInputError("cubic curvature requires two control points")
        return Curve._create(
            curve_type,
            tuple(
                (_number(item[0], "cubic.x"), _number(item[1], "cubic.y"))
                for item in params
            ),
        )
    raise GeometryInputError(f"unsupported curvature type: {curve_type}")


def _parse_stitch(value: object) -> Stitch:
    if not isinstance(value, list) or len(value) not in (2, 3):
        raise GeometryInputError("stitch must contain two references")
    first = _parse_stitch_ref(value[0])
    second = _parse_stitch_ref(value[1])
    right_wrong = len(value) == 3 and value[2] == "right_wrong"
    if len(value) == 3 and not right_wrong:
        raise GeometryInputError("stitch has an unsupported flag")
    return Stitch._create(first, second, right_wrong)


def _parse_stitch_ref(value: object) -> StitchRef:
    if not isinstance(value, Mapping):
        raise GeometryInputError("stitch reference must be a mapping")
    piece = value.get("panel")
    edge = value.get("edge")
    if not isinstance(piece, str) or not isinstance(edge, int) or isinstance(edge, bool) or edge < 0:
        raise GeometryInputError("stitch reference is invalid")
    return StitchRef._create(piece, edge)


def _validate_stitch_references(
    stitches: tuple[Stitch, ...], pieces: tuple[Piece, ...]
) -> None:
    edge_counts = {piece.name: len(piece.edges) for piece in pieces}
    for stitch in stitches:
        for reference in (stitch.first, stitch.second):
            if reference.piece not in edge_counts or reference.edge >= edge_counts[reference.piece]:
                raise GeometryInputError("stitch reference points to an unknown edge")


def _calculate_bounds(pieces: tuple[Piece, ...]) -> Bounds:
    points = []
    for piece in pieces:
        angle = radians(piece.rotation[2])
        for vertex in piece.vertices:
            points.append(
                Point._create(
                    piece.translation.x + vertex.x * cos(angle) - vertex.y * sin(angle),
                    piece.translation.y + vertex.x * sin(angle) + vertex.y * cos(angle),
                )
            )
    if not points:
        raise GeometryInputError("assembly.pattern.panels must not be empty")
    return Bounds._create(
        Point._create(min(point.x for point in points), min(point.y for point in points)),
        Point._create(max(point.x for point in points), max(point.y for point in points)),
    )


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise GeometryInputError(f"{name} must be a finite number")
    return float(value)


def _optional_string(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GeometryInputError("labels must be strings")
    return value


def _point_to_mapping(point: Point) -> dict[str, float]:
    return {"x": point.x, "y": point.y}


def _piece_to_mapping(piece: Piece) -> dict[str, object]:
    return {
        "name": piece.name,
        "label": piece.label,
        "vertices": [_point_to_mapping(point) for point in piece.vertices],
        "edges": [
            {
                "start": edge.start,
                "end": edge.end,
                "label": edge.label,
                "curve": _curve_to_mapping(edge.curve),
            }
            for edge in piece.edges
        ],
        "translation": _point_to_mapping(piece.translation),
        "rotation": list(piece.rotation),
    }


def _curve_to_mapping(curve: Optional[Curve]) -> Optional[dict[str, object]]:
    if curve is None:
        return None
    return {"type": curve.type, "params": [list(item) if isinstance(item, tuple) else item for item in curve.params]}


def _stitch_to_mapping(stitch: Stitch) -> dict[str, object]:
    return {
        "first": {"piece": stitch.first.piece, "edge": stitch.first.edge},
        "second": {"piece": stitch.second.piece, "edge": stitch.second.edge},
        "right_wrong": stitch.right_wrong,
    }


__all__ = ["GeometryDocument", "GeometryInputError", "serialize_geometry"]
