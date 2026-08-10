# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Boundaries

This Claude operates **only within `zmlx/demo/`**. Do not modify any file outside this directory.

Two other Claudes manage sibling domains:
- **C++ Claude**: `zml/` (C++ kernel headers, `zml.dll`)
- **Python Claude**: `zmlx/` (the rest of the Python package)

The demo directory consumes `zmlx` as a library. If you need API changes in `zmlx/`, describe them and let the Python Claude implement them.

## How demos are discovered and loaded

The GUI's `DemoView` (`zmlx/ui/widget/demo_view.py`) calls `zmlx.demo.list_demo_files()` defined in `demo/__init__.py`. This function:

1. Scans all `.py` files under this directory using `zmlx.alg.list_files`
2. **Excludes** files whose path contains `__Trash` or `debugging`
3. Extracts all `# **` comment lines and `exec()`s the content after `# **` as Python code (via `zmlx.alg.code_config`, which uses Python's `tokenize` module)
4. Checks if `desc` is defined in the resulting namespace and is a non-empty string
5. Returns `[(absolute_path, description), ...]`

**Every runnable demo MUST define `desc` via `# ** desc = '...'`.** Each `# **` line is independently `exec()`d, so every line must be valid standalone Python. Files without a `desc` variable are invisible in the GUI.

Multi-line descriptions are possible via Python implicit string concatenation on one `# **` line:
```python
# ** desc = 'line1\n' 'line2\n' 'line3'
```

## Running demos

```bash
# GUI mode (default) — opens the GUI, runs in a console tab
python zmlx/demo/flow_1ph/darcy_1d.py

# Headless mode — runs without GUI, saves plots to file
python zmlx/demo/flow_1ph/darcy_1d.py --no-gui
```

The standard entry-point pattern:
```python
if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

`gui.execute()` handles both GUI and headless modes automatically (the `--no-gui` flag is checked inside `gui.execute`). Never call `gui.execute()` inside a function — only in `if __name__ == '__main__'`.

## Batch testing

```bash
python test_all_demos.py              # all demos, parallel (CPU core count)
python test_all_demos.py --jobs 8     # 8 threads
python test_all_demos.py --timeout 30 # 30s timeout per demo
python test_all_demos.py --verbose    # show stdout from each demo
```

`test_all_demos.py` runs each demo as a subprocess with `--no-gui`, captures stdout/stderr, and generates a report. Timeout and failures are tallied separately. Output goes to `test_output_<timestamp>/`.

## Directory organization

| Directory | Domain | Typical APIs |
|-----------|--------|--------------|
| `flow_1ph/` | Single-phase Darcy flow, diffusion | `Seepage` (manual), `tfc.create` |
| `flow_2ph/` | Two-phase displacement, gravity segregation | `tfc.create`, `FluDef`, `create_kr` |
| `thermal/` | Pure heat conduction, EGS | `model.iterate_thermal()` |
| `hydrate/` | Hydrate formation & production | `hydrate.create`, `hydrate.solve` |
| `heavy_oil/` | In-situ conversion (ICP) | `icp.create` |
| `mech/` | Solid mechanics (FEM) | FEM modules |
| `spring/` | Spring-mass dynamics | FEM dynamics |
| `flow_dy/` | Fluid inertia / pressure waves | `tfc.create(dt_max=...)` |
| `flow_thermal/` | Flow + heat coupling | `tfc.create(heat_cond=...)` |
| `aqueous/` | Aqueous convection-diffusion | `tfc.create`, multi-component |
| `plt/` | Matplotlib plotting demos | `fig`, `plot` |
| `others/` | Miscellaneous (DFN, IP, sand, etc.) | Various |
| `tests/` | Low-level DLL/function tests | Direct `zml` calls |

Subdirectories named `__Trash/` contain deprecated code — do not reference or revive. They are excluded from `list_demo_files()`.

## Demo structure conventions

**High-level demos** (the majority) use `tfc.create()` or scene-specific helpers (`hydrate.create()`, `icp.create()`):
```python
model = tfc.create(mesh, porosity=..., p=..., s=..., perm=...,
                   fludefs=[...], gravity=(0,0,-10), dt_max=...)
tfc.solve(model, time_forward=..., folder='output')
```

**Low-level demos** (teaching/debugging) manually build `Seepage` with `add_cell()` / `add_face()`:
```python
model = Seepage()
c = model.add_cell(); c.pos = [x, y, z]; c.set_pore(...)
face = model.add_face(i0, i1); face.cond = area * perm / dist
model.iterate(dt=...)
```

Key formula: `face.cond = area * perm / dist` — the conductivity coefficient governing flow between two cells.

## Spatial function pattern

The core modeling paradigm is defining physics properties as `(x, y, z) → value` closures:
```python
def get_k(x, y, z):
    return 1e-14 if -70 < z < -30 else 1e-15   # reservoir vs seal

def get_s(x, y, z):
    return {'ch4': 0.5, 'h2o': 0.5}
```

These are passed to `tfc.create(porosity=..., perm=..., s=..., p=..., temperature=...)`.

## Boundary condition patterns (in code, not config)

- **Constant pressure**: Set cell volume to `1e6` (huge) → pressure barely changes during flow
- **Constant temperature**: Set `denc` to `1e20` (huge heat capacity)
- **Closed boundary**: No face connection (or `perm=0`)
- **Wells**: `model.add_injector(cell=..., flu=..., value=rate)` or `prods=[{'index': ..., 'p': [...]}]` in scene creators

## Visualization

```python
# Inside a demo:
def show(model, jx, jz):
    x = tfc.get_x(model, shape=(jx, jz))
    p = tfc.get_p(model, shape=(jx, jz))
    # ... plot via fig or plot module

tfc.solve(model, extra_plot=lambda: show(model, jx, jz), ...)

# Or use plot() which auto-adapts to GUI/headless:
plot(on_figure, caption='Results')
```

## Path helpers

- `demo/opath.py` — re-exports `zmlx.io.path.opath` and `zmlx.io.path.set_path` for output paths
- `demo/path.py` — `SelfPath(__file__)` for getting the demo root path (use `get_path()`)
- `demo/get_path.py` — deprecated alias for `demo/path.py`, remove after 2026-04-15

## Files excluded from demo listing

- Any file in a path containing `__Trash` (deprecated code)
- Any file in a path containing `debugging` (work-in-progress)
- `test_all_demos.py` itself (not a demo, it's the test runner)

## When creating or modifying a demo

1. First line must be `# ** desc = 'concise Chinese description'`
2. Follow the existing `gui.execute(main, close_after_done=False)` entry pattern
3. Import from `zmlx` via `from zmlx import *` (the standard in existing demos)
4. Keep code self-contained and well-commented in Chinese
5. Use `tfc.create()` (high-level) unless the demo specifically teaches low-level mechanics
6. Add the demo to the appropriate subdirectory matching its physics domain
7. Never import from or modify files outside `zmlx/demo/`
