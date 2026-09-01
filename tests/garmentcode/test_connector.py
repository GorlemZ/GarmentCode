import pytest

from pygarment.garmentcode.connector import StitchingRule
from pygarment.garmentcode.edge_factory import EdgeSeqFactory
from pygarment.garmentcode.interface import Interface
from pygarment.garmentcode.panel import Panel


pytestmark = pytest.mark.core


def panel_with_side(name, length):
    panel = Panel(name)
    panel.edges = EdgeSeqFactory.from_verts([0, 0], [length, 0], [length, 1], [0, 1], loop=True)
    panel.assembly()
    return panel, Interface(panel, panel.edges[0])


def test_stitching_rule_serializes_panel_names_edge_ids_and_right_wrong_flag():
    first_panel, first_interface = panel_with_side("front", 10)
    second_panel, second_interface = panel_with_side("back", 10)
    second_interface.right_wrong[0] = True

    stitches = StitchingRule(first_interface, second_interface).assembly()

    assert stitches == [
        [
            {"panel": first_panel.name, "edge": 0},
            {"panel": second_panel.name, "edge": 0},
            "right_wrong",
        ]
    ]


def test_stitching_rule_subdivides_longer_side_to_match_shorter_side():
    first_panel, first_interface = panel_with_side("front", 10)
    second_panel = Panel("back")
    second_panel.edges = EdgeSeqFactory.from_verts([0, 0], [4, 0], [10, 0], [10, 1], [0, 1], loop=True)
    second_panel.assembly()
    second_interface = Interface(second_panel, second_panel.edges[:2])

    rule = StitchingRule(first_interface, second_interface)

    assert rule.isMatching()
    assert len(first_interface.edges) == 2
    assert len(second_interface.edges) == 2
