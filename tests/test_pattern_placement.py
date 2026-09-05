"""Geometry of the sewing pattern overlay in the GUI canvas.

These tests cover ``gui.pattern_placement`` only: pure math, no NiceGUI. The
regression values were measured in the browser after fixing the overlay
layout for NiceGUI 3 (see CHANGELOG) and are identical on NiceGUI 2.24 and 3.16.
"""
import pytest

from gui.pattern_placement import (
    CanvasConfig,
    PatternPlacement,
    compute_pattern_placement,
)

pytestmark = pytest.mark.core

# [min_x, max_x, min_y, max_y] in cm, body axis at x=0, feet at y=0, y grows down
TSHIRT_BBOX = [-37.6, 122.9, -141.8, -91.4]
TSHIRT_SIZE = [160.6, 50.4]

# FittedShirt + StraightWB + full-length Pants: overflows the canvas at the bottom
LONG_OUTFIT_BBOX = [-30.5, 109.5, -141.7, 24.9]
LONG_OUTFIT_SIZE = [140.0, 166.7]


def _assert_within_left_top_right(p: PatternPlacement):
    """The bottom edge cannot be checked: the image height follows its aspect ratio."""
    assert 0. <= p.left
    assert 0. <= p.top
    assert 0. < p.width
    assert p.left + p.width <= 1.


def test_tshirt_fits_without_rescaling():
    p = compute_pattern_placement(TSHIRT_BBOX, TSHIRT_SIZE)

    assert not p.is_rescaled
    assert p.body_scale == 1.0
    _assert_within_left_top_right(p)
    assert p.left == pytest.approx(0.1606, abs=1e-3)
    assert p.top == pytest.approx(0.1659, abs=1e-3)
    assert p.width == pytest.approx(0.4668, abs=1e-3)


def test_tshirt_fixture_values_match_generated_pattern(tshirt_pattern, tmp_path):
    """The hard-coded bbox values above are what pygarment produces.

    margin=0 must stay aligned with the GUI call site (gui/gui_pattern.py):
    svg_bbox_size includes twice the margin.
    """
    tshirt_pattern.get_svg(str(tmp_path / "t-shirt.svg"), with_text=False, view_ids=False, flat=False, margin=0)

    assert list(tshirt_pattern.svg_bbox) == pytest.approx(TSHIRT_BBOX, abs=0.1)
    assert list(tshirt_pattern.svg_bbox_size) == pytest.approx(TSHIRT_SIZE, abs=0.1)


def test_long_outfit_rescales_body_and_pattern_together():
    cfg = CanvasConfig()
    p = compute_pattern_placement(LONG_OUTFIT_BBOX, LONG_OUTFIT_SIZE, cfg)

    assert p.is_rescaled
    assert 0. < p.body_scale < 1.
    _assert_within_left_top_right(p)
    assert p.body_scale == pytest.approx(0.8573, abs=1e-3)
    assert p.left == pytest.approx(0.2268, abs=1e-3)
    assert p.top == pytest.approx(0.2361, abs=1e-3)
    assert p.width == pytest.approx(0.3489, abs=1e-3)

    # The pattern width shrinks by the same factor as the body
    assert p.width == pytest.approx(
        LONG_OUTFIT_SIZE[0] * cfg.cm_to_canvas * cfg.w_rel_body_size * p.body_scale)


def test_width_is_body_relative_and_pad_independent():
    cfg = CanvasConfig()
    no_pad = CanvasConfig(w_canvas_pad=0., h_canvas_pad=0.)

    with_pad = compute_pattern_placement(TSHIRT_BBOX, TSHIRT_SIZE, cfg)
    without_pad = compute_pattern_placement(TSHIRT_BBOX, TSHIRT_SIZE, no_pad)

    expected_width = TSHIRT_SIZE[0] * cfg.cm_to_canvas * cfg.w_rel_body_size
    assert with_pad.width == pytest.approx(expected_width)
    assert without_pad.width == pytest.approx(expected_width)
    # Pads only shift the pattern
    assert without_pad.left - with_pad.left == pytest.approx(cfg.w_canvas_pad)
    assert without_pad.top - with_pad.top == pytest.approx(cfg.h_canvas_pad)


def test_left_edge_follows_body_axis():
    """The pattern's x=0 (body axis) lands on the silhouette axis of the canvas."""
    cfg = CanvasConfig(w_canvas_pad=0.)
    p = compute_pattern_placement(TSHIRT_BBOX, TSHIRT_SIZE, cfg)

    axis_in_canvas = p.left + abs(TSHIRT_BBOX[0]) * cfg.cm_to_canvas * cfg.w_rel_body_size
    assert axis_in_canvas == pytest.approx(cfg.body_canvas_center)


def test_wide_pattern_rescales_horizontally():
    """A very wide pattern (long shirt + full circle skirt) triggers the rescale.

    The rescale picks the single worst overflow, so extremely wide patterns are
    shrunk but not guaranteed to fit horizontally (pre-existing behaviour):
    only the left/top edges are checked here.
    """
    bbox = [-117.6, 360.5, -141.4, 27.9]
    size = [478.1, 169.2]
    p = compute_pattern_placement(bbox, size)

    assert p.is_rescaled
    assert 0. < p.body_scale < 1.
    assert 0. <= p.left
    assert 0. <= p.top
