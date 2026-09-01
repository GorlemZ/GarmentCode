import math

import numpy as np
import pytest

from pygarment.garmentcode.edge import CurveEdge, Edge
from pygarment.garmentcode.edge_factory import CircleEdgeFactory, EdgeFactory, EdgeSeqFactory


pytestmark = pytest.mark.core


def test_linear_edge_length_and_reverse_preserve_geometry():
    edge = Edge([0, 0], [3, 4])

    assert edge.length() == pytest.approx(5)
    assert edge.midpoint().tolist() == pytest.approx([1.5, 2])

    edge.reverse()

    assert edge.start == [3, 4]
    assert edge.end == [0, 0]
    assert edge.length() == pytest.approx(5)


def test_quadratic_curve_preserves_endpoints_and_is_longer_than_shortcut():
    edge = CurveEdge([0, 0], [10, 0], [[0.5, 0.5]])
    curve = edge.as_curve()

    assert [curve.start.real, curve.start.imag] == pytest.approx([0, 0])
    assert [curve.end.real, curve.end.imag] == pytest.approx([10, 0])
    assert edge.length() > Edge([0, 0], [10, 0]).length()


def test_cubic_curve_assembly_serializes_control_points():
    edge = CurveEdge([0, 0], [10, 0], [[0.25, 0.5], [0.75, -0.5]])

    endpoints, data = edge.assembly()

    assert endpoints == [[0, 0], [10, 0]]
    assert data["curvature"] == {
        "type": "cubic",
        "params": [[0.25, 0.5], [0.75, -0.5]],
    }


def test_subdivision_preserves_length_and_chaining():
    edge = Edge([0, 0], [10, 0])

    pieces = edge.subdivide_len([0.25, 0.25, 0.5])

    assert len(pieces) == 3
    assert pieces.isChained()
    assert pieces.length() == pytest.approx(edge.length())
    assert pieces.lengths() == pytest.approx([2.5, 2.5, 5.0])


def test_edge_factory_round_trips_svg_line():
    edge = Edge([0, 0], [5, 0])

    rebuilt = EdgeFactory.from_svg_curve(edge.as_curve())

    assert isinstance(rebuilt, Edge)
    assert rebuilt.start == pytest.approx(edge.start)
    assert rebuilt.end == pytest.approx(edge.end)


def test_fraction_factory_rejects_fractions_that_do_not_sum_to_one():
    with pytest.raises(RuntimeError, match="fraction is incorrect"):
        EdgeSeqFactory.from_fractions([0, 0], [10, 0], [0.5, 0.25])


def test_circle_factory_from_radius_creates_expected_arc_length():
    radius = 10
    half_circle = CircleEdgeFactory.from_rad_length(radius, math.pi * radius)

    assert half_circle.length() == pytest.approx(math.pi * radius, rel=1e-3)
    assert half_circle.as_radius_angle()[0] == pytest.approx(radius)
