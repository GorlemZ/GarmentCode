# Installation

GarmentCode supports Python 3.9 and newer. Python 3.11 is the recommended development version.

## Choose the capability you need

- **PyGarment core** builds and serializes parametric sewing patterns.
- **Repository examples and GUI** additionally use the files under `assets/` and should be run from a checkout of this repository.
- **3D simulation** requires the GarmentCode fork of NVIDIA Warp and is not provided by the standard Python package installation.
- **Maya + Qualoth** is a legacy integration with separate proprietary prerequisites.

## System Cairo dependency

CairoSVG requires the native Cairo library.

### macOS

```bash
brew install cairo
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix cairo)/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
```

Add the `export` line to your shell profile if Python otherwise reports that it cannot find `cairo`, `libcairo-2`, or `libcairo.2.dylib`.

### Debian/Ubuntu

```bash
sudo apt-get update
sudo apt-get install -y libcairo2
```

### Fedora

```bash
sudo dnf install cairo
```

### Windows

Install a native Cairo runtime matching your Python/Windows architecture and make its DLL directory available on `PATH` before importing PyGarment. The universal PyGarment wheel intentionally does not bundle platform-specific Cairo DLLs. See the [CairoSVG documentation](https://cairosvg.org/documentation/) for current Windows prerequisites.

## Install the core package

From PyPI:

```bash
python -m pip install pygarment
```

For development from a repository checkout, `uv` is recommended:

```bash
uv venv --python 3.11
uv pip install -e ".[dev]"
```

Alternatively, use the standard library virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Verify the installation from outside the repository root so the checkout cannot mask a broken installation:

```bash
cd /tmp  # Windows: change to any directory outside the checkout
python -c "import pygarment; print(pygarment.__file__)"
```

The printed path should point to the active environment's `site-packages/pygarment` directory (or to the editable-install mapping when developing locally).

## Configure repository scripts

Copy the system-path template before running GUI, sampling, fitting, or simulation scripts:

```bash
cp system.template.json system.json
```

Update these fields for your machine:

- `output`: one-off script output and logs;
- `datasets_path`: generated sewing-pattern datasets;
- `datasets_sim`: simulation results;
- `sim_configs_path`: simulation/render configuration files;
- `bodies_default_path`: bundled or custom base body models;
- `body_samples_path`: sampled body-shape datasets.

The default relative paths in `system.template.json` are suitable for the bundled examples, but dataset paths must be supplied before running the data-generation pipeline.

## Run the core example and GUI

Run repository entry points from the repository root because the examples use repository-level `assets/` paths:

```bash
python test_garmentcode.py
python gui.py
```

See [Running GarmentCode](Running_garmentcode.md) for usage details.

## Install the simulator

GarmentCode uses its own version of [NVIDIA Warp](https://github.com/maria-korosteleva/NvidiaWarp-GarmentCode). Build and install that fork manually before using the draping and dataset-simulation commands. A normal `pip install pygarment` does not install or configure this external simulator.

See [Running data generation](Running_data_generation.md) for the pipeline and configuration format.

## Troubleshooting

See [Troubleshooting](Troubleshooting.md) for Cairo loader errors, incorrect package imports, missing `system.json`, and optional simulation prerequisites.
