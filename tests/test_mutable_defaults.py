import ast
from pathlib import Path


def _function_defaults(path):
    module = ast.parse(Path(path).read_text())
    defaults = {}
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults[node.name] = node.args.defaults
    return defaults


def _is_mutable_literal(node):
    return isinstance(node, (ast.List, ast.Dict, ast.Set))


def test_no_mutable_default_arguments_in_remaining_p3_targets():
    repo = Path(__file__).resolve().parents[1]

    targets = {
        repo / 'pygarment/mayaqltools/mayascene.py': {
            'load',
            'add_colliders',
            'intersect_colliders_3D',
            '_setSimProps',
            '_add_simple_camera',
        },
        repo / 'pygarment/mayaqltools/scan_imitation.py': {
            '_camera_surface',
            'remove_invisible',
        },
        repo / 'pygarment/meshgen/boxmeshgen.py': {
            'save_box_mesh_obj',
        },
    }

    mutable_defaults = []
    for path, function_names in targets.items():
        defaults = _function_defaults(path)
        for function_name in function_names:
            for default in defaults[function_name]:
                if _is_mutable_literal(default):
                    mutable_defaults.append(f'{path.name}:{function_name}')

    assert mutable_defaults == []
