# Troubleshooting

## CairoSVG cannot load Cairo

Typical errors mention `cairo`, `cairo-2`, `libcairo-2`, or `libcairo.2.dylib`.

On macOS with Homebrew:

```bash
brew install cairo
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix cairo)/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}"
python -c "import cairosvg; print(cairosvg.__file__)"
```

On Debian/Ubuntu, install `libcairo2`; on Fedora, install `cairo`. On Windows, install a native Cairo runtime matching the system architecture and expose its DLL directory on `PATH`; the universal PyGarment wheel does not bundle platform-specific native libraries.

## `import pygarment` fails after installation

First verify where Python is looking from a directory outside the checkout:

```bash
cd /tmp
python -c "import sys; print(sys.executable); import pygarment; print(pygarment.__file__)"
```

If the import resolves to the repository while testing a wheel, the checkout is shadowing the installed package. Create a fresh virtual environment, install the wheel, and repeat the command outside the repository.

If the wheel contains top-level `garmentcode`, `pattern`, or `meshgen` directories instead of `pygarment/`, it was built with the old package layout. Rebuild from a revision containing the corrected `pyproject.toml`.

## Repository scripts cannot find `system.json`

Create the local configuration from the template:

```bash
cp system.template.json system.json
```

Then run repository scripts from the repository root. `system.json` is intentionally ignored by Git because it contains machine-specific paths.

## Repository scripts cannot find files under `assets/`

The example programs and GUI use repository-level assets and are not standalone wheel entry points. Run them from a complete checkout with the repository root as the current working directory.

## Simulation import or runtime fails

The standard package does not install the GarmentCode Warp simulator. Build and install [NvidiaWarp-GarmentCode](https://github.com/maria-korosteleva/NvidiaWarp-GarmentCode) and verify its GPU/runtime prerequisites separately.

Core pattern generation does not require Warp. Use the core smoke test to separate packaging problems from simulator problems:

```bash
pytest tests/test_core_smoke.py -v
```

## Maya or Qualoth imports fail

`pygarment.mayaqltools` is a legacy integration and imports Autodesk Maya APIs that are only available inside a compatible Maya environment. See [Running Maya + Qualoth](Running_Maya_Qualoth.md); these imports are not part of the core package smoke test.
