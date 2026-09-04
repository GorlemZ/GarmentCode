# P3 Boundary Split: `meshgen/sim_config.py` Implementation Plan

> **For Hermes:** execute as a low-risk refactor slice with strict TDD and an adversarial review pass before commit.

**Goal:** separate path/file-locator responsibilities from simulation-parameter normalization without breaking existing imports.

**Architecture:** keep `SimConfig` in `pygarment/meshgen/sim_config.py`, move `PathCofig` into a dedicated module such as `pygarment/meshgen/path_config.py`, and leave a compatibility re-export in `sim_config.py` during the first slice. This reduces mixed responsibilities while avoiding a cross-repo rename blast radius.

**Tech Stack:** Python, existing `Properties` loader, pytest, Ruff.

---

## Current findings

`pygarment/meshgen/sim_config.py` currently mixes two unrelated concerns:
1. `PathCofig`: filesystem path derivation, timestamped output directories, body/spec/design file resolution, `system.json` lookup.
2. `SimConfig`: simulation option/material normalization and derived limits (`min_sim_steps`, timeouts, attachment settings).

Observed consumers of `PathCofig` span:
- `pygarment/meshgen/boxmeshgen.py`
- `pygarment/meshgen/datasim_utils.py`
- `pygarment/meshgen/garment.py`
- `pygarment/meshgen/render/pythonrender.py`
- `pygarment/meshgen/simulation.py`
- `test_garment_sim.py`

This makes a rename of the misspelled public class name too risky for the first split. Keep the public symbol unchanged in slice 1.

---

## Proposed low-risk slice

### Step 1: Add a source-level regression test
**Objective:** prove that `PathCofig` and `SimConfig` remain importable from their expected entrypoints during the split.

**Files:**
- Create/modify: `tests/test_boundaries.py`

**Test shape:**
- AST or import-level test asserting:
  - `pygarment.meshgen.sim_config` still exposes `PathCofig`
  - `pygarment.meshgen.sim_config` still exposes `SimConfig`
  - `PathCofig` source definition moves out of `sim_config.py`

**Validation:**
- Run only the new test first and confirm RED before implementation if checking for the moved definition.

### Step 2: Extract `PathCofig`
**Objective:** move filesystem concerns into `pygarment/meshgen/path_config.py`.

**Files:**
- Create: `pygarment/meshgen/path_config.py`
- Modify: `pygarment/meshgen/sim_config.py`

**Implementation notes:**
- Copy `PathCofig` exactly first; avoid behavior changes.
- Preserve the public class name `PathCofig` in the new module for compatibility.
- In `sim_config.py`, replace the class body with `from pygarment.meshgen.path_config import PathCofig` plus `SimConfig`.
- Do not rename `PathCofig` to `PathConfig` in this slice.

### Step 3: Keep compatibility imports stable
**Objective:** avoid wide churn in downstream modules.

**Files:**
- Prefer no downstream import rewrites in slice 1.

**Implementation notes:**
- Existing imports `from pygarment.meshgen.sim_config import PathCofig` should continue to work unchanged.
- Optional follow-up slice can migrate direct consumers to `path_config.py` once CI is green.

### Step 4: Verify no behavioral drift
**Objective:** ensure extraction is structural only.

**Validation:**
- `pytest tests/test_boundaries.py -q`
- `pytest tests/test_mutable_defaults.py tests/test_exceptions.py -q`
- `pytest -m core -q`
- `ruff check pygarment/meshgen/sim_config.py pygarment/meshgen/path_config.py tests --select I,F401,F841,W605`

### Step 5: Adversarial review before commit
**Objective:** challenge the split for hidden breakage.

**Checklist:**
- Does any code rely on `PathCofig.__module__ == 'pygarment.meshgen.sim_config'`?
- Does `Properties('./system.json')` become harder to resolve after extraction?
- Did the move accidentally introduce import cycles with `meshgen` modules?
- Did the shim preserve public import paths for scripts outside the package?
- Did we quietly expand scope by renaming the typo or changing path semantics?

If any answer is yes, stop and reduce the slice further.

---

## Adversarial review of this plan

### Risk 1: the split might break reflection or pickle/import-path assumptions
**Fix applied:** keep `PathCofig` name unchanged and re-export it from `sim_config.py` in slice 1 instead of renaming it.

### Risk 2: moving the class might accidentally change runtime path resolution
**Fix applied:** no path logic changes in the first slice; pure move first, cleanup later.

### Risk 3: the repo has missing optional dependencies, so import-based tests may become noisy
**Fix applied:** keep tests narrow to `meshgen.sim_config`/AST-level assertions and the already-green core suite.

### Risk 4: broad consumer rewrites create unnecessary churn
**Fix applied:** defer downstream import rewrites; compatibility shim first.

---

## Success criteria

- `PathCofig` defined in `pygarment/meshgen/path_config.py`
- `SimConfig` remains in `pygarment/meshgen/sim_config.py`
- `from pygarment.meshgen.sim_config import PathCofig, SimConfig` still works
- targeted tests pass
- no new Ruff findings in the touched files
