import xml.etree.ElementTree as ET

import pytest

from pygarment.pattern.core import EmptyPatternError
from pygarment.pattern.wrappers import VisPattern

pytestmark = pytest.mark.core


def test_svg_contains_one_filled_path_per_tshirt_panel(tshirt_pattern, tmp_path):
    svg_file = tmp_path / "tshirt.svg"

    drawing = tshirt_pattern.get_svg(str(svg_file), with_text=False, view_ids=False, flat=True)
    drawing.save()

    root = ET.parse(svg_file).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    paths = root.findall(".//svg:path", namespace)

    assert len(paths) == len(tshirt_pattern.pattern["panels"])


def test_empty_svg_raises_empty_pattern_error(tmp_path):
    empty = VisPattern()

    with pytest.raises(EmptyPatternError):
        empty.get_svg(str(tmp_path / "empty.svg"))
