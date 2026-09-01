import os
import subprocess
import venv
import zipfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.packaging


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_wheel_installs_pygarment_namespace(tmp_path):
    wheel_under_test = os.environ.get("WHEEL_UNDER_TEST")
    if wheel_under_test:
        wheel = Path(wheel_under_test)
    else:
        wheel_dir = tmp_path / "wheel"
        wheel_dir.mkdir()
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(wheel_dir)],
            cwd=PROJECT_ROOT,
            check=True,
        )
        wheel = next(wheel_dir.glob("*.whl"))

    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        assert "pygarment/__init__.py" in members
        assert "pygarment/data_config.py" in members
        assert "pygarment/garmentcode/component.py" in members
        assert "pygarment/pattern/core.py" in members
        native_suffixes = (".dll", ".dylib", ".pyd", ".so")
        assert not any(member.lower().endswith(native_suffixes) for member in members)
        assert "garmentcode/__init__.py" not in members
        assert "pattern/core.py" not in members

        wheel_metadata = next(
            member for member in members if member.endswith(".dist-info/WHEEL")
        )
        wheel_metadata_text = archive.read(wheel_metadata).decode("utf-8")
        assert "Root-Is-Purelib: true" in wheel_metadata_text
        assert "Tag: py3-none-any" in wheel_metadata_text

    environment = tmp_path / "environment"
    venv.EnvBuilder(with_pip=False).create(environment)
    python = (
        environment / "Scripts/python.exe"
        if os.name == "nt"
        else environment / "bin/python"
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(wheel)],
        check=True,
    )

    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            python,
            "-c",
            (
                "import pygarment; "
                "from pygarment.garmentcode.component import Component; "
                "from pygarment.pattern.core import BasicPattern; "
                "print(pygarment.__file__)"
            ),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert str(environment) in result.stdout
    assert str(PROJECT_ROOT) not in result.stdout
