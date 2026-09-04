import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def tshirt_garment():
    import yaml

    from assets.bodies.body_params import BodyParameters
    from assets.garment_programs.meta_garment import MetaGarment

    body = BodyParameters(PROJECT_ROOT / "assets/bodies/mean_all.yaml")
    with (PROJECT_ROOT / "assets/design_params/t-shirt.yaml").open(
        encoding="utf-8"
    ) as design_file:
        design = yaml.safe_load(design_file)["design"]
    return MetaGarment("t-shirt", body, design)


@pytest.fixture(scope="session")
def tshirt_pattern(tshirt_garment):
    return tshirt_garment.assembly()
