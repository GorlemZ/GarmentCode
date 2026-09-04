import ast
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from assets.garment_programs.meta_garment import (
    IncorrectElementConfiguration,
    TotalLengthError,
)
from pygarment.pattern.core import EmptyPatternError
from pygarment.pattern.wrappers import VisPattern

pytestmark = pytest.mark.core


def test_empty_pattern_error_is_a_regular_exception(tmp_path):
    empty = VisPattern()

    with pytest.raises(Exception):
        empty.get_svg(str(tmp_path / "empty.svg"))

    assert issubclass(EmptyPatternError, Exception)


def test_meta_garment_errors_are_regular_exceptions():
    assert issubclass(TotalLengthError, Exception)
    assert issubclass(IncorrectElementConfiguration, Exception)


def test_meshgen_and_maya_sources_use_regular_exceptions_and_not_baseexception():
    repo = Path(__file__).resolve().parents[1]
    targets = {
        repo / 'pygarment/mayaqltools/mayascene.py': {'PatternLoadingError'},
        repo / 'pygarment/meshgen/boxmeshgen.py': {
            'PatternLoadingError',
            'MultiStitchingError',
            'StitchingError',
            'DegenerateTrianglesError',
            'NormError',
        },
        repo / 'pygarment/meshgen/simulation.py': {
            'SimulationError',
            'FrameTimeOutError',
            'SimTimeOutError',
        },
    }

    bad_bases = []
    broad_catches = []

    for path, expected_classes in targets.items():
        module = ast.parse(path.read_text())
        seen = set()

        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef) and node.name in expected_classes:
                seen.add(node.name)
                if any(isinstance(base, ast.Name) and base.id == 'BaseException' for base in node.bases):
                    bad_bases.append(f'{path.name}:{node.name}')
            if isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Name) and node.type.id == 'BaseException':
                broad_catches.append(f'{path.name}:{node.lineno}')

        assert seen == expected_classes

    assert bad_bases == []
    assert broad_catches == []


def test_run_sim_propagates_keyboardinterrupt(monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    module_path = repo / 'pygarment/meshgen/simulation.py'

    warp_module = types.ModuleType('warp')
    warp_module.init = lambda: None
    monkeypatch.setitem(sys.modules, 'warp', warp_module)

    trimesh_module = types.ModuleType('trimesh')
    monkeypatch.setitem(sys.modules, 'trimesh', trimesh_module)

    render_module = types.ModuleType('pygarment.meshgen.render.pythonrender')
    render_module.render_images = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, 'pygarment.meshgen.render.pythonrender', render_module)

    garment_module = types.ModuleType('pygarment.meshgen.garment')

    class FakeCloth:
        def __init__(self, cloth_name, config, paths, caching=False):
            self.frame = -1

        def run_frame(self):
            raise KeyboardInterrupt()

    garment_module.Cloth = FakeCloth
    monkeypatch.setitem(sys.modules, 'pygarment.meshgen.garment', garment_module)

    spec = importlib.util.spec_from_file_location('test_meshgen_simulation_module', module_path)
    simulation = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(simulation)

    class FakeProps(dict):
        def __init__(self):
            super().__init__(
                sim={
                    'config': {'options': {}, 'material': {}, 'max_sim_steps': 1},
                    'stats': {'sim_time': {}, 'spf': {}, 'fin_frame': {}, 'body_collisions': {}, 'self_collisions': {}},
                },
                render={'config': {}},
            )
            self.fail_calls = []

        def add_fail(self, section_name, fail_type, info):
            self.fail_calls.append((section_name, fail_type, info))

    props = FakeProps()

    with pytest.raises(KeyboardInterrupt):
        simulation.run_sim('dress', props, object())

    assert props.fail_calls == []
