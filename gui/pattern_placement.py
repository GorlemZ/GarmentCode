"""Pure geometry for placing the sewing pattern image over the body silhouette.

All values are fractions of the canvas (the millimeter-paper background image),
so they are independent of the viewport size. Kept free of NiceGUI imports so
it can be unit-tested in the core test suite.
"""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasConfig:
    """Constants describing how the body silhouette sits on the canvas."""
    w_rel_body_size: float = 0.5        # Body height as a fraction of the canvas width
    h_rel_body_size: float = 0.95       # Body height as a fraction of the canvas height
    cm_to_canvas: float = 1 / 171.99    # Inverse of the mean_all body height (cm) from GGG
    body_canvas_center: float = 0.273   # Body vertical axis as a fraction of the canvas width
    # Empirical shifts of the pattern, retuned (from 0.011 / 0.04) after the overlay
    # stopped inheriting Quasar's 16px padding, so that the t-shirt lands where
    # NiceGUI 2.x drew it at 1920x1080.
    w_canvas_pad: float = 0.003
    h_canvas_pad: float = 0.026
    scale_margin: float = 1.2           # Extra room when the pattern overflows the canvas


@dataclass(frozen=True)
class PatternPlacement:
    """Where to put the pattern image, as fractions of the canvas."""
    left: float
    top: float
    width: float
    body_scale: float = 1.0     # Scale applied to the body silhouette (1.0 = untouched)
    is_rescaled: bool = False   # True when the overflow branch was taken


def compute_pattern_placement(
        svg_bbox: Sequence[float],
        svg_bbox_size: Sequence[float],
        cfg: CanvasConfig = CanvasConfig()) -> PatternPlacement:
    """Align the pattern svg with the body silhouette.

    svg_bbox is [min_x, max_x, min_y, max_y] of the pattern in cm, in a frame
    where the body stands at x=0 with feet at y=0 (y grows downwards, so the
    shoulder line is a negative min_y). svg_bbox_size is the svg viewbox size
    in cm, i.e. the bbox extent plus twice the svg margin: the GUI renders with
    margin=0, so the two coincide.

    When the pattern does not fit, both body and pattern are shrunk by the same
    factor so that the pattern stays inside the canvas.
    """
    w_shift = abs(svg_bbox[0])   # Body axis location w.r.t. the left edge of the pattern
    top_cm = abs(svg_bbox[2])    # Height of the pattern top above the feet
    p_w, p_h = svg_bbox_size[0], svg_bbox_size[1]

    m_top = (1. - top_cm * cfg.cm_to_canvas) * cfg.h_rel_body_size + (1. - cfg.h_rel_body_size) / 2
    m_left = cfg.body_canvas_center - w_shift * cfg.cm_to_canvas * cfg.w_rel_body_size
    m_right = 1 - m_left - p_w * cfg.cm_to_canvas * cfg.w_rel_body_size
    m_bottom = 1 - m_top - p_h * cfg.cm_to_canvas * cfg.h_rel_body_size

    # Canvas padding adjustment
    m_top -= cfg.h_canvas_pad
    m_left -= cfg.w_canvas_pad
    m_right += cfg.w_canvas_pad   # preserve evaluated width
    m_bottom -= cfg.h_canvas_pad

    if m_top >= 0 and m_bottom >= 0 and m_left >= 0 and m_right >= 0:
        return PatternPlacement(left=m_left, top=m_top, width=1. - m_right - m_left)

    # Pattern overflows: shrink body and pattern together
    y_top_scale = abs(min(m_top * cfg.scale_margin, 0.)) + 1.
    y_bot_scale = 1. + abs(min(m_bottom * cfg.scale_margin, 0.))
    x_left_scale = abs(min(m_left * cfg.scale_margin, 0.)) + 1.
    x_right_scale = abs(min(m_right * cfg.scale_margin, 0.)) + 1.
    scale = min(1. / y_top_scale, 1. / y_bot_scale, 1. / x_left_scale, 1. / x_right_scale)

    body_center = 0.5 - cfg.body_canvas_center
    m_top = (1. - top_cm * cfg.cm_to_canvas) * cfg.h_rel_body_size * scale \
        + (1. - cfg.h_rel_body_size * scale) / 2
    m_left = (0.5 - body_center * scale) - w_shift * cfg.cm_to_canvas * cfg.w_rel_body_size * scale
    m_right = 1 - m_left - p_w * cfg.cm_to_canvas * cfg.w_rel_body_size * scale

    # Canvas padding adjustment (the top one is not needed here: the body is
    # scaled around the canvas center, which already moves the shoulder line down)
    m_left -= cfg.w_canvas_pad * scale
    m_right += cfg.w_canvas_pad * scale

    return PatternPlacement(
        left=m_left, top=m_top, width=1. - m_right - m_left,
        body_scale=scale, is_rescaled=True)
