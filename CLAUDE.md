# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**IGG-Hydrate** (package name `IggHydrate`, imported as `zmlx`) is a reservoir multi-field coupling simulator developed at IGGCAS. It models Thermal-Hydraulic-Mechanical-Chemical (THMC) processes for natural gas hydrates, shale oil, carbon sequestration, and general subsurface flow.

- **Primary repo**: `https://gitee.com/geomech/hydrate` (GitHub mirror is read-only)
- **Author**: Zhaobin Zhang (zhangzhaobin@mail.iggcas.ac.cn)
- **License**: Free for academic use; commercial use requires contacting the author

### Naming conventions

- **Package name** (`pyproject.toml`): `IggHydrate` — this is what `pip install` sees
- **Import name**: `zmlx` — this is what Python code imports (`import zmlx`)
- **C++ kernel**: `zml` — the compiled binary is `zml.dll` / `zml.so`; `zmlx/exts/` wraps it, and `import zmlx.exts as zml` gives direct access to the C++ binding layer
- **`zml.py`** at the project root is a **deprecated shim** that warns and redirects to `zmlx`. It will be removed after 2027-05-25. Do not add new code that imports `zml` directly — always use `zmlx`

## Day-to-day commands

### Running the application

```bash
python -m zmlx ui          # Open the GUI
python -m zmlx demo        # Open the demo browser (recommended starting point)
python -m zmlx ver         # Show version info
python -m zmlx env         # Install all Python dependencies via pip
python -m zmlx help        # List all CLI commands
```

### Installing dependencies

```bash
python zmlx/script/install_dep.py
```

If pip downloads are slow in China, run `python zmlx/script/write_pip_config.py` first to configure the Tsinghua mirror.

### Running tests

Tests are standalone scripts in `tests/` subdirectories (`if __name__ == '__main__':`). Before release, run all demos via `python zmlx/demo/test_all_demos.py` (parallel subprocess, `--no-gui`, `--jobs N`, `--timeout N`). Individual tests:
```bash
python <test_file>.py
```

## Stability and backward compatibility

**zmlx is a foundational library** — downstream projects depend on its public API. `zmlx/__init__.py` defines every symbol they can import.

- **Additive changes only**: new parameters (with defaults), new functions, new optional arguments. Never remove, rename, or change the signature of anything exported from `zmlx/__init__.py`.
- **Internal refactoring is fine** as long as the external API is unchanged.
- **Small, incremental changes**: modify 1–2 files at a time, then run relevant tests. Large refactors require a written plan and user approval first.

## Architecture

This is a **hybrid C++/Python** codebase with a strict layered design:

```
Layer 5: Application scenarios     zmlx/scen/         hydrate, icp, frac, geothermal_helium, ...
Layer 4: Coupled physics engine    zmlx/tfc/          Thermal-Flow-Chemical iteration loop
Layer 3: Utilities & GUI           zmlx/utility/, ui/ Field definitions, PyQt6 GUI, controllers
Layer 2: Physics definitions       zmlx/fluid/, react/, kr/  Fluid props, reactions, relative permeability
Layer 1: Python→C++ bindings       zmlx/exts/         Thin wrappers around zml.dll / zml.so
Layer 0: C++ kernel                ../../zml/          C++17 header-only library
```

### Key design principles

- **`Seepage`** is the central data structure — stores all cell/face/fluid data and iteration state. `tfc.seepage.iterate()` advances a simulation by one timestep, orchestrating all coupled physics.
- **`zmlx/exts/` is a minimal binding layer**: one DLL export → one Python function. Complex logic lives in higher layers.
- **Dependency order**: `system/` → `exts/` → everything else. `ui/` is moving toward independence.

### Key directories

| Directory | Purpose |
|-----------|---------|
| `zmlx/exts/` | C++ bindings + compiled `.dll`/`.so` |
| `zmlx/tfc/` | TFC coupling engine (iterate loop, core utilities) |
| `zmlx/fluid/` | Fluid properties (CH₄, CO₂, H₂O, oil, kerogen, hydrate) |
| `zmlx/react/` | Chemical reaction rates |
| `zmlx/ui/` | PyQt6 GUI (~35 widgets) |
| `zmlx/scen/` | Application scenarios |
| `zmlx/demo/` | Demo scripts (~30) — start here to learn the API |
| `zmlx/fem/` | Finite element method |
| `zmlx/plt/`, `zmlx/fig/` | Visualization (matplotlib) |
| `zmlx/geometry/` | Geometric primitives (angles, distances, DFN) |
| `zmlx/utility/` | Field interpolation, controllers, monitors |
| `zmlx/seepage_mesh/` | Mesh generation |
| `../../zml/` | C++17 header-only kernel |

### Gotchas

- **No Chinese characters in the install path** — causes unpredictable C++ kernel errors.
- **Deprecated**: `zmlx/config/` (use `zmlx/tfc/`), `zmlx/base/`, `zml.py` (shim, removed after 2027-05-25).

## Development guidelines

### Adding a new feature

1. Implement in the appropriate submodule (`zmlx/tfc/` for coupling, `zmlx/fluid/` for fluid, etc.)
2. If public, add an **additive-only** export in `zmlx/__init__.py`. If internal, keep it in the submodule.
3. Match existing code style (docstrings, type hints, naming).
4. Add or update a test script in the corresponding `tests/` directory.
5. CLI commands: register in `zmlx/__init__.py` via `_cmds['name'] = func` or `@_cmds.register('name', desc='...')`.

### Anti-patterns (do NOT)

- **Modify** C++ files in `../../zml/` or `.dll`/`.so` binaries — the C++ kernel is maintained separately. If a C++ change is required, explain what needs to change and why; the author will handle it.
- **Delete** existing test scripts — add new ones instead
- **Import** from `zml` directly — always use `zmlx`
- **Add** new dependencies to `zmlx/exts/` — the binding layer must stay thin
- **Push** — requires the user to perform manually

## Coding style

These conventions are distilled from the existing codebase. Match them when writing or refactoring code.

### Module structure

Module-level docstring → imports (stdlib → typing → zmlx → local) → code → `if __name__ == "__main__":` test/entry block at bottom.

### Imports

- **Order**: stdlib → typing → zmlx → local.
- **Warnings**: `import zmlx.alg.sys as warnings` (NOT `import warnings`).
- **C++ bindings**: `from zmlx.exts import ...`.
- **Circular imports**: import from higher-level modules inside the function body, not at top level.

### Docstrings

- Use triple double-quotes `"""..."""`.
- Module-level docstrings describe the module's role (Chinese is standard).
- Function docstrings use **Google-style**: `"""简述。\n\nArgs:\n    param1: 说明\n    param2: 说明（含默认值）\n\nReturns:\n    返回值说明\n"""`

### Function signatures

- Type hints on all public parameters. `Optional[X]` for nullable params. `*` separator for keyword-only config args. `None` defaults for optional objects.

### Error handling

- Assertions at function boundaries: `assert isinstance(obj, ExpectedType), f'...'`
- Try/except for external ops (I/O, matplotlib); `warnings.warn(f'...{err}...')` for non-fatal errors.

### Naming

`snake_case` for functions/variables, `PascalCase` for classes, `_underscore` prefix for private modules, no prefix for public packages.

### Common utilities

`@clock` (timing), `@execute_once`, `@deprecated(...)`, `app_data.getenv`, `make_parent`, `gui.exists()`/`gui.break_point()`, `log(...)`.

### Formatting

No hard line-length limit. Multi-line imports use parentheses. One blank line between top-level definitions. Comments in Chinese.
