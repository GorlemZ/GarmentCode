"""Geometry of the sewing pattern overlay in the GUI canvas.

These tests cover ``gui.pattern_placement`` only: pure math, no NiceGUI. The
expected numbers below are the function's own outputs for the fixtures; the
rendered DOM was checked to match them on NiceGUI 2.24 and 3.16 (2026-09-05).
"""
import random

import pytest

from gui.gui_pattern import SVG_DISPLAY_KWARGS
from gui.pattern_placement import CanvasConfig, compute_pattern_placement

pytestmark = pytest.mark.core

# [min_x, max_x, min_y, max_y] in cm, body axis at x=0, feet at y=0, y grows down
TSHIRT_BBOX = [-37.6, 122.9, -141.8, -91.4]
TSHIRT_SIZE = [160.6, 50.4]

# FittedShirt + StraightWB + full-length Pants: reaches almost to the canvas bottom
LONG_OUTFIT_BBOX = [-30.5, 109.5, -141.7, 24.9]
LONG_OUTFIT_SIZE = [140.0, 166.7]

# Shirt + full circle skirt: much wider than the canvas
WIDE_OUTFIT_BBOX = [-117.6, 360.5, -141.4, 27.9]
WIDE_OUTFIT_SIZE = [478.1, 169.2]

CFG = CanvasConfig()


def _shoulder_y(bbox, cfg=CFG):
    return cfg.silhouette_feet - abs(bbox[2]) * cfg.cm_body


def _scaled(value, scale):
    """A canvas fraction after scaling about the canvas center."""
    return 0.5 + (value - 0.5) * scale


def test_tshirt_fixture_values_match_generated_pattern(tshirt_pattern):
    """The hard-coded bbox values above are what pygarment produces with the GUI settings."""
    tshirt_pattern.get_svg("unused.svg", **SVG_DISPLAY_KWARGS)

    assert list(tshirt_pattern.svg_bbox) == pytest.approx(TSHIRT_BBOX, abs=0.1)
    assert list(tshirt_pattern.svg_bbox_size) == pytest.approx(TSHIRT_SIZE, abs=0.1)


def test_tshirt_fits_without_rescaling():
    p = compute_pattern_placement(TSHIRT_BBOX, TSHIRT_SIZE)

    assert not p.is_rescaled
    assert p.left == pytest.approx(0.1562, abs=1e-3)
    assert p.top == pytest.approx(0.1659, abs=1e-3)
    assert p.width == pytest.approx(0.4669, abs=1e-3)
    assert p.height == pytest.approx(0.2442, abs=1e-3)


def test_long_outfit_fits_without_rescaling():
    """Tall garments use the real image height (width-driven aspect), not an inflated estimate."""
    p = compute_pattern_placement(LONG_OUTFIT_BBOX, LONG_OUTFIT_SIZE)

    assert not p.is_rescaled
    assert p.top == pytest.approx(0.1664, abs=1e-3)
    assert p.bottom == pytest.approx(0.9741, abs=1e-3)
    assert p.bottom <= 1. - CFG.fit_margin


def test_wide_outfit_rescales_to_fit():
    p = compute_pattern_placement(WIDE_OUTFIT_BBOX, WIDE_OUTFIT_SIZE)

    assert p.is_rescaled
    assert p.body_scale == pytest.approx(0.59, abs=1e-2)
    assert p.left >= CFG.fit_margin
    assert p.right == pytest.approx(1. - CFG.fit_margin)


def test_pattern_axis_and_shoulder_follow_the_silhouette():
    """Body axis x=0 lands on the silhouette axis; the top sits shoulder_gap above the shoulder."""
    for bbox, size in [(TSHIRT_BBOX, TSHIRT_SIZE), (LONG_OUTFIT_BBOX, LONG_OUTFIT_SIZE),
                       (WIDE_OUTFIT_BBOX, WIDE_OUTFIT_SIZE)]:
        p = compute_pattern_placement(bbox, size)
        s = p.body_scale

        axis_in_pattern = p.left + abs(bbox[0]) * CFG.cm_x * s
        assert axis_in_pattern == pytest.approx(_scaled(CFG.body_axis_x, s))
        assert p.top == pytest.approx(_scaled(_shoulder_y(bbox) - CFG.shoulder_gap, s))


def test_rescaled_patterns_always_fit_inside_the_margin():
    """Property: for any bbox the placed rect stays within [fit_margin, 1 - fit_margin]."""
    rng = random.Random(0)
    lo, hi = CFG.fit_margin - 1e-9, 1. - CFG.fit_margin + 1e-9
    rescaled = 0
    for _ in range(2000):
        min_x = -rng.uniform(0., 400.)
        width = rng.uniform(10., 900.)
        min_y = -rng.uniform(80., 200.)
        height = rng.uniform(10., 400.)
        p = compute_pattern_placement([min_x, min_x + width, min_y, min_y + height], [width, height])

        assert lo <= p.left and p.right <= hi
        assert lo <= p.top and p.bottom <= hi
        assert 0. < p.body_scale <= 1.
        rescaled += p.is_rescaled
    assert rescaled > 0   # the sample exercised the overflow branch


def test_width_is_pattern_size_times_body_scale():
    p = compute_pattern_placement(WIDE_OUTFIT_BBOX, WIDE_OUTFIT_SIZE)

    assert p.width == pytest.approx(WIDE_OUTFIT_SIZE[0] * CFG.cm_x * p.body_scale)
    assert p.height == pytest.approx(WIDE_OUTFIT_SIZE[1] * CFG.cm_y * p.body_scale)


def test_config_rejects_width_limited_silhouette():
    with pytest.raises(ValueError):
        CanvasConfig(silhouette_aspect=1.0)
