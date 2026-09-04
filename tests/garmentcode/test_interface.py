import numpy as np
import pytest

from pygarment.garmentcode.edge import Edge
from pygarment.garmentcode.edge_factory import EdgeSeqFactory
from pygarment.garmentcode.interface import Interface
from pygarment.garmentcode.panel import Panel

pytestmark = pytest.mark.core


def panel_with_edge():
    panel = Panel("panel")
    edge = Edge([0, 0], [10, 0])
    panel.edges = EdgeSeqFactory.from_verts([0, 0], [10, 0], [10, 1], [0, 1], loop=True)
    return panel, edge


def test_interface_projects_ruffle_lengths_without_mutating_source_edge():
    panel, edge = panel_with_edge()
    interface = Interface(panel, edge, ruffle=2)

    projected = interface.projecting_edges()

    assert projected.length() == pytest.approx(5)
    assert edge.length() == pytest.approx(10)


def test_interface_oriented_edges_marks_flipped_copies_only():
    panel, edge = panel_with_edge()
    interface = Interface(panel, edge)
    interface.edges_flipping[0] = True

    oriented = interface.oriented_edges()

    assert oriented[0].flipped is True
    assert oriented[0].start == [10, 0]
    assert oriented[0].end == [0, 0]
    assert edge.start == [0, 0]
    assert edge.end == [10, 0]


def test_interface_projecting_fractions_are_normalized():
    panel = Panel("panel")
    edges = EdgeSeqFactory.from_verts([0, 0], [3, 0], [3, 4])
    interface = Interface(panel, edges)

    assert interface.projecting_fractions() == pytest.approx(np.array([3 / 7, 4 / 7]))
