"""Pure geometry for placing the sewing pattern image over the body silhouette.

All values are fractions of the canvas (the millimeter-paper background image),
so they are independent of the viewport size. Kept free of NiceGUI imports so
it can be unit-tested in the core test suite.

Frame conventions
-----------------
* The silhouette (``assets/img/ggg_outline_mean_all.svg``) is rendered by a
  Quasar ``q-img`` with ``object-fit: cover`` into the canvas. Its viewBox is
  wider than the canvas, so the fit is height-limited: vertical fractions of
  the viewBox carry over to the canvas unchanged and the sides are cropped.
* The pattern svg uses a frame where the body axis is x=0 and the feet are at
  y=0, y growing downwards (so the shoulder line is a negative ``min_y``).
* When the pattern does not fit, body and pattern are shrunk by the same
  factor about the canvas center (the body via a CSS ``transform: scale``
  with ``transform-origin: center``).
"""
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CanvasConfig:
    """Constants describing the canvas and the silhouette asset drawn on it."""
    canvas_aspect: float = 1500. / 900.          # Millimeter paper (assets/img/millimiter_paper_1500_900.png)
    body_height_cm: float = 171.99               # mean_all body height (GGG), the one the silhouette depicts

    # Silhouette asset geometry, from the path bounding boxes of the svg
    # (viewBox 1920x1080): figure spans y 32.3..1022.6, its vertical axis is x=537.9.
    silhouette_aspect: float = 1920. / 1080.
    silhouette_head: float = 32.3 / 1080.
    silhouette_feet: float = 1022.6 / 1080.
    silhouette_axis: float = 537.9 / 1920.

    w_rel_body_size: float = 0.5     # Pattern scale: body height (cm) as a fraction of the canvas width
    shoulder_gap: float = 0.025      # Pattern top floats this far above the shoulder line (aesthetic,
                                     # reproduces the NiceGUI 2.x rendering at 1920x1080)
    fit_margin: float = 0.02         # Kept free around the pattern when rescaling to fit

    def __post_init__(self):
        if self.silhouette_aspect < self.canvas_aspect:
            raise ValueError('Silhouette placement assumes a height-limited cover fit '
                             '(silhouette_aspect >= canvas_aspect)')

    # Derived frame quantities (fractions of the canvas)
    @property
    def body_axis_x(self) -> float:
        """Silhouette axis in canvas-width fractions, after the cover-fit crop."""
        cover = self.silhouette_aspect / self.canvas_aspect
        return self.silhouette_axis * cover - (cover - 1.) / 2.

    @property
    def cm_x(self) -> float:
        """Canvas-width fraction per cm of pattern."""
        return self.w_rel_body_size / self.body_height_cm

    @property
    def cm_y(self) -> float:
        """Canvas-height fraction per cm of pattern (the image keeps its aspect ratio)."""
        return self.cm_x * self.canvas_aspect

    @property
    def cm_body(self) -> float:
        """Canvas-height fraction per cm of the silhouette."""
        return (self.silhouette_feet - self.silhouette_head) / self.body_height_cm


@dataclass(frozen=True)
class PatternPlacement:
    """Where to put the pattern image, as fractions of the canvas."""
    left: float
    top: float
    width: float
    height: float
    body_scale: float = 1.0   # Scale applied to body and pattern about the canvas center

    @property
    def is_rescaled(self) -> bool:
        return self.body_scale < 1.0

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height


def compute_pattern_placement(
        svg_bbox: Sequence[float],
        svg_bbox_size: Sequence[float],
        cfg: CanvasConfig = CanvasConfig()) -> PatternPlacement:
    """Align the pattern svg with the body silhouette.

    svg_bbox is [min_x, max_x, min_y, max_y] of the pattern in cm (see frame
    conventions in the module docstring). svg_bbox_size is the svg viewbox size
    in cm, i.e. the bbox extent plus twice the svg margin: the GUI renders with
    margin=0, so the two coincide.

    The pattern's body axis lands on the silhouette axis and its top edge sits
    ``shoulder_gap`` above the silhouette shoulder line. If the result exceeds
    the canvas minus ``fit_margin`` on any side, body and pattern are scaled
    about the canvas center by the largest factor that fits all four sides.
    """
    w_shift = abs(svg_bbox[0])   # Body axis location w.r.t. the left edge of the pattern
    top_cm = abs(svg_bbox[2])    # Height of the pattern top above the feet
    p_w, p_h = svg_bbox_size[0], svg_bbox_size[1]

    # Unscaled placement
    shoulder_y = cfg.silhouette_feet - top_cm * cfg.cm_body
    top = shoulder_y - cfg.shoulder_gap
    left = cfg.body_axis_x - w_shift * cfg.cm_x
    width = p_w * cfg.cm_x
    height = p_h * cfg.cm_y

    # Largest scale (about the canvas center) that keeps every edge inside
    # [fit_margin, 1 - fit_margin]. An edge already on the correct side of the
    # center never constrains the scale.
    room = 0.5 - cfg.fit_margin
    scale = 1.
    for edge in (left, top):
        if edge < 0.5:
            scale = min(scale, room / (0.5 - edge))
    for edge in (left + width, top + height):
        if edge > 0.5:
            scale = min(scale, room / (edge - 0.5))

    if scale >= 1.:
        return PatternPlacement(left=left, top=top, width=width, height=height)

    return PatternPlacement(
        left=0.5 + (left - 0.5) * scale,
        top=0.5 + (top - 0.5) * scale,
        width=width * scale,
        height=height * scale,
        body_scale=scale,
    )
