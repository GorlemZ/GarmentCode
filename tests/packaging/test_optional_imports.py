import email.parser
import os
import subprocess
import venv
import zipfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.packaging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_RUNTIME_DEPS = [
    "pyyaml>=6.0",
    "numpy<2",
    "scipy",
    "svgwrite",
    "svgpathtools",
    "psutil",
]
OPTIONAL_IMPORT_MODULES = [
    "cairosvg",
    "matplotlib",
    "nicegui",
    "trimesh",
    "igl",
    "CGAL",
    "pyrender",
    "warp",
    "maya",
]
OPTIONAL_DISTRIBUTIONS = {
    "cairosvg",
    "matplotlib",
    "nicegui",
    "trimesh",
    "libigl",
    "cgal",
    "pyrender",
    "pillow",
}
EXTRA_REQUIREMENTS = {
    "visualization": {"cairosvg", "matplotlib"},
    "gui": {"nicegui", "cairosvg", "matplotlib"},
    "mesh": {"trimesh", "libigl", "cgal", "pyrender", "pillow", "matplotlib"},
    "simulation": set(),
    "maya": set(),
    "dev": {"pytest", "ruff", "twine", "uv"},
}

@pytest.fixture(scope="session")
def project_wheel(tmp_path_factory):
    wheel_under_test = os.environ.get("WHEEL_UNDER_TEST")
    if wheel_under_test:
        return Path(wheel_under_test)

    wheel_dir = tmp_path_factory.mktemp("optional-import-wheel")
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(wheel_dir)],
        cwd=PROJECT_ROOT,
        check=True,
    )
    return next(wheel_dir.glob("*.whl"))


def _metadata_from_wheel(wheel):
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            member for member in archive.namelist() if member.endswith(".dist-info/METADATA")
        )
        return email.parser.Parser().parsestr(archive.read(metadata_name).decode())


def _create_venv(path):
    venv.EnvBuilder(with_pip=False).create(path)
    return path / "Scripts/python.exe" if os.name == "nt" else path / "bin/python"


def _without_checkout_pythonpath():
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return environment


def test_base_metadata_excludes_optional_runtime_dependencies(project_wheel):
    metadata = _metadata_from_wheel(project_wheel)
    base_requirements = [
        requirement
        for requirement in metadata.get_all("Requires-Dist", [])
        if "extra ==" not in requirement
    ]

    for distribution in OPTIONAL_DISTRIBUTIONS:
        assert not any(requirement.lower().startswith(distribution) for requirement in base_requirements)

    optional_extras = set(metadata.get_all("Provides-Extra", []))
    assert {"visualization", "gui", "mesh", "simulation", "maya", "dev"}.issubset(optional_extras)

    requirements = metadata.get_all("Requires-Dist", [])
    for extra, distributions in EXTRA_REQUIREMENTS.items():
        extra_requirements = [
            requirement.lower()
            for requirement in requirements
            if f'extra == "{extra}"' in requirement
        ]
        for distribution in distributions:
            assert any(requirement.startswith(distribution) for requirement in extra_requirements), extra


def test_base_install_imports_core_without_optional_dependencies(project_wheel, tmp_path):
    environment = tmp_path / "base-env"
    python = _create_venv(environment)

    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), *BASE_RUNTIME_DEPS],
        check=True,
        env=_without_checkout_pythonpath(),
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(project_wheel)],
        check=True,
        env=_without_checkout_pythonpath(),
    )

    probe = tmp_path / "outside-checkout"
    probe.mkdir()
    result = subprocess.run(
        [
            str(python),
            "-c",
            """
import importlib.util
import json
import pygarment as pyg
from pygarment.garmentcode.component import Component
from pygarment.pattern.core import BasicPattern

pattern = Component('empty').assembly()
optional = {name: importlib.util.find_spec(name) is None for name in %r}
print(json.dumps({
    'pygarment_file': pyg.__file__,
    'pattern_type': type(pattern).__name__,
    'optional_missing': optional,
}))
"""
            % OPTIONAL_IMPORT_MODULES,
        ],
        cwd=probe,
        text=True,
        capture_output=True,
        env=_without_checkout_pythonpath(),
        check=True,
    )

    assert str(PROJECT_ROOT) not in result.stdout
    assert '"pattern_type": "VisPattern"' in result.stdout
    for module in OPTIONAL_IMPORT_MODULES:
        assert f'"{module}": true' in result.stdout


def test_png_export_reports_visualization_extra_when_cairosvg_is_missing(project_wheel, tmp_path):
    environment = tmp_path / "base-env"
    python = _create_venv(environment)

    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), *BASE_RUNTIME_DEPS],
        check=True,
        env=_without_checkout_pythonpath(),
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(project_wheel)],
        check=True,
        env=_without_checkout_pythonpath(),
    )

    result = subprocess.run(
        [
            str(python),
            "-c",
            """
from pygarment.pattern.wrappers import VisPattern
pattern = VisPattern()
pattern.name = 'square'
pattern.pattern['panels'] = {
    'square': {
        'translation': [0, 0, 0],
        'rotation': [0, 0, 0],
        'vertices': [[0, 0], [10, 0], [10, 10], [0, 10]],
        'edges': [
            {'endpoints': [0, 1]},
            {'endpoints': [1, 2]},
            {'endpoints': [2, 3]},
            {'endpoints': [3, 0]},
        ],
    }
}
pattern._save_as_image('square.svg', 'square.png')
""",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        env=_without_checkout_pythonpath(),
    )

    assert result.returncode != 0
    assert "pygarment[visualization]" in result.stderr
    assert "CairoSVG" in result.stderr


def test_advertised_extras_resolve_from_built_wheel(project_wheel, tmp_path):
    environment = tmp_path / "extras-env"
    python = _create_venv(environment)
    wheel_url = project_wheel.resolve().as_uri()

    for extra in ["visualization", "gui", "mesh", "simulation", "maya", "dev"]:
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--dry-run",
                f"pygarment[{extra}] @ {wheel_url}",
            ],
            check=True,
            env=_without_checkout_pythonpath(),
        )
