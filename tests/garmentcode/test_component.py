import numpy as np
import pytest

from pygarment.garmentcode.component import Component
from pygarment.garmentcode.edge_factory import EdgeSeqFactory
from pygarment.garmentcode.panel import Panel


pytestmark = pytest.mark.core


def panel(name, x):
    panel = Panel(name)
    panel.edges = EdgeSeqFactory.from_verts([0, 0], [2, 0], [2, 2], [0, 2], loop=True)
    panel.translate_to([x, 0, 0])
    return panel


def test_component_assembly_merges_subcomponent_panels_without_stitches():
    component = Component("shirt")
    component.subs = [panel("front", 0), panel("back", 5)]

    pattern = component.assembly()

    assert pattern.name == "shirt"
    assert set(pattern.pattern["panels"]) == {"front", "back"}
    assert pattern.pattern["stitches"] == []


def test_component_translation_moves_all_subcomponents_by_same_delta():
    front = panel("front", 0)
    back = panel("back", 5)
    component = Component("shirt")
    component.subs = [front, back]

    component.translate_by([1, 2, 3])

    assert front.translation == pytest.approx([1, 2, 3])
    assert back.translation == pytest.approx([6, 2, 3])


def test_empty_component_has_infinite_bbox_sentinel():
    bbox_min, bbox_max = Component("empty").bbox3D()

    assert np.isposinf(bbox_min).all()
    assert np.isneginf(bbox_max).all()
