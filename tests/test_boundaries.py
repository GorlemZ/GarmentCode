import ast
import importlib
from pathlib import Path

import pytest

from pygarment.meshgen.path_config import PathCofig
from pygarment.meshgen.sim_config import SimConfig

pytestmark = pytest.mark.core


def test_path_config_split_keeps_sim_config_compatibility():
    repo = Path(__file__).resolve().parents[1]
    sim_config_path = repo / 'pygarment/meshgen/sim_config.py'
    path_config_path = repo / 'pygarment/meshgen/path_config.py'
    sim_config_module = importlib.import_module('pygarment.meshgen.sim_config')
    path_config_module = importlib.import_module('pygarment.meshgen.path_config')

    sim_module = ast.parse(sim_config_path.read_text())
    path_module = ast.parse(path_config_path.read_text())

    sim_classes = {node.name for node in ast.walk(sim_module) if isinstance(node, ast.ClassDef)}
    path_classes = {node.name for node in ast.walk(path_module) if isinstance(node, ast.ClassDef)}

    assert 'PathCofig' not in sim_classes
    assert 'PathCofig' in path_classes
    assert sim_config_module.PathCofig is path_config_module.PathCofig
    assert PathCofig.__module__ == 'pygarment.meshgen.path_config'
    assert SimConfig.__module__ == 'pygarment.meshgen.sim_config'
