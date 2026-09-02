# Dependency groups

GarmentCode separates the reusable 2D pattern-programming library from heavier repository capabilities. Install only the capability you need.

## Base install

```bash
python -m pip install pygarment
```

The base package supports:

- `import pygarment`;
- the 2D garment DSL (`Edge`, `Panel`, `Component`, `Interface`, `Stitches`, factories and operators);
- JSON pattern loading and serialization;
- SVG path generation through `svgwrite` and `svgpathtools`.

The base install intentionally does **not** require:

- CairoSVG or native Cairo for PNG/PDF export;
- Matplotlib for 3D debug plots;
- NiceGUI for the web configurator;
- trimesh, libigl, CGAL, pyrender, or Pillow for mesh generation/rendering;
- NVIDIA Warp for simulation;
- Autodesk Maya or Qualoth for legacy tools.

## Extras

| Extra | Command | Purpose | Notes |
|---|---|---|---|
| `visualization` | `python -m pip install "pygarment[visualization]"` | PNG/PDF export and 3D debug image generation | CairoSVG still needs a native Cairo runtime installed on the operating system. |
| `gui` | `python -m pip install "pygarment[gui]"` | NiceGUI-based 2D configurator UI | Run from a full repository checkout because the GUI uses `assets/` paths. 3D draping also needs `mesh` and the external Warp fork. |
| `mesh` | `python -m pip install "pygarment[mesh]"` | Box-mesh generation and mesh rendering dependencies available from Python packages: trimesh, libigl, CGAL, pyrender, Pillow, and Matplotlib | Platform wheels for libigl/CGAL may vary; install failures are environment-specific and should not block the core package. |
| `simulation` | `python -m pip install "pygarment[simulation]"` | Declares the Warp-backed simulation capability boundary | Install the GarmentCode-specific NVIDIA Warp environment manually from `maria-korosteleva/NvidiaWarp-GarmentCode`; this extra is a documentation marker, not a PyPI dependency bundle. |
| `maya` | `python -m pip install "pygarment[maya]"` | Declares the legacy Maya capability boundary | Maya and Qualoth are proprietary external prerequisites and are not installed by pip. |
| `dev` | `python -m pip install -e ".[dev]"` | Tests, lint, package build/check tooling | Use from a repository checkout. |

## Runtime errors for missing extras

Optional capabilities fail lazily with an actionable `ImportError` when their dependency is first used. For example, PNG/PDF export without `visualization` reports that `CairoSVG` is required and suggests:

```bash
python -m pip install "pygarment[visualization]"
```

This is intentional: importing and using the core DSL should stay lightweight, while heavier rendering, GUI, meshing, simulation, and legacy integrations remain explicit.

## CI coverage

The package workflow verifies both conditions:

1. built wheel metadata keeps optional distributions out of base `Requires-Dist`;
2. a base virtual environment with only base runtime dependencies can import and assemble core PyGarment objects from the wheel outside the source checkout.
