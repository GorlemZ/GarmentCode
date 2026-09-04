import pytest
from scipy.spatial.transform import Rotation as R

from pygarment.garmentcode.edge_factory import EdgeSeqFactory
from pygarment.garmentcode.panel import Panel

pytestmark = pytest.mark.core


def rectangle_panel(name="front", width=4, height=6):
    panel = Panel(name)
    panel.edges = EdgeSeqFactory.from_verts(
        [0, 0], [width, 0], [width, height], [0, height], loop=True
    )
    return panel


def test_panel_translation_preserves_2d_dimensions_in_3d_bbox():
    panel = rectangle_panel(width=4, height=6)

    panel.translate_to([10, 20, 30])
    bbox_min, bbox_max = panel.bbox3D()

    assert bbox_max - bbox_min == pytest.approx([4, 6, 0])
    assert bbox_min == pytest.approx([10, 20, 30])


def test_panel_rotation_preserves_edge_lengths():
    panel = rectangle_panel(width=4, height=6)
    before = panel.edges.lengths()

    panel.rotate_by(R.from_euler("XYZ", [0, 0, 90], degrees=True))

    assert panel.edges.lengths() == pytest.approx(before)


def test_panel_assembly_assigns_edge_ids_and_closes_loop():
    panel = rectangle_panel()

    pattern = panel.assembly()
    serialized = pattern.pattern["panels"]["front"]

    assert len(serialized["vertices"]) == 4
    assert len(serialized["edges"]) == 4
    assert serialized["edges"][-1]["endpoints"][-1] == 0
    assert [edge.geometric_id for edge in panel.edges] == [0, 1, 2, 3]


def test_panel_mirror_flips_x_translation_and_preserves_lengths():
    panel = rectangle_panel().translate_to([7, 0, 0])
    before_lengths = panel.edges.lengths()

    panel.mirror()

    assert panel.translation[0] == pytest.approx(-7)
    assert panel.edges.lengths() == pytest.approx(before_lengths)
