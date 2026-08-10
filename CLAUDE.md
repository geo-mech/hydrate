# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**IGG-Hydrate** (package `IggHydrate`, import `zmlx`) is a reservoir multi-field coupling simulator. It models Thermal-Hydraulic-Mechanical-Chemical (THMC) processes.

### Names

| Name | Meaning |
|------|---------|
| `IggHydrate` | Package name (`pip install`) |
| `zmlx` | Python import name |
| `zml` | C++ kernel (`.dll`/`.so`); `import zmlx.exts as zml` binds to it |
| `zml.py` (root) | Deprecated shim, removed after 2027-05-25 — always use `zmlx` |

## Architecture

Hybrid C++/Python, strict layering:

```
Layer 5: Scenarios        zmlx/scen/
Layer 4: Physics engine    zmlx/tfc/          Seepage.iterate()
Layer 3: Utilities & GUI   zmlx/ui/, plt/
Layer 2: Physics models    zmlx/fluid/, react/
Layer 1: C++ bindings      zmlx/exts/         (thin, one export per function)
Layer 0: C++ kernel        ../../zml/          (DO NOT MODIFY)
```

- **`Seepage`** = central data structure (cells, faces, fluids, iteration state)
- **`zmlx/exts/`** must stay thin — complex logic goes in higher layers
- **Dependency**: `system/` → `exts/` → everything else

## Key directories

| Directory | Purpose |
|-----------|---------|
| `zmlx/exts/` | C++ bindings |
| `zmlx/tfc/` | TFC coupling engine |
| `zmlx/fluid/` | Fluid props (H₂O, CH₄, CO₂, etc.) — see `fluid/ReadMe.md` |
| `zmlx/fluid/cp/` | CoolProp engine: density, viscosity, specific heat (8 fluids, < 0.1%) |
| `zmlx/fluid/rkt/` | Reaktoro engine: density, specific heat (7 fluids, Supcrt98) |
| `zmlx/fluid/rkt/aq/` | Reaktoro aqueous solutions: gas-water density |
| `zmlx/ui/` | PyQt6 GUI |
| `zmlx/demo/` | Demo scripts (~30) — learn the API here |
| `zmlx/scen/` | Application scenarios |
| `zmlx/fem/` | Finite element |
| `zmlx/plt/`, `zmlx/fig/` | Visualization |

## GUI mode

### Entry point pattern

Use `gui.execute()` **only** in `if __name__ == '__main__'` blocks:

```python
def main():
    """Business logic — runs on GUI thread."""
    gui.break_point()              # Allow pause/stop in long loops
    gui.progress('Computing', [0, 100], step)

if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
```

Never call `gui.execute()` inside a function — it will nest and behave unpredictably.

### `gui.*` functions (auto no-op in headless mode)

| Function | Purpose |
|----------|---------|
| `gui.break_point()` | Pause/stop checkpoint |
| `gui.progress(label, range, value)` | Progress bar |
| `gui.information(text)` | Info dialog |
| `gui.question(text)` | Yes/no dialog |
| `gui.show_attrs(**attrs)` | Dynamic variable display |
| `gui.in_dark_mode()` | Check dark mode (GUI only) |

### Matplotlib plotting: `zmlx.ui.plot`

The standard way to produce matplotlib figures is via a callback + `zmlx.ui.plot()`:

```python
from zmlx.ui import plot

def on_figure(fig):
    ax = fig.add_subplot(111)
    ax.plot(x, y)

plot(on_figure, caption="Results")
```

`zmlx.ui.plot` auto-adapts:

| Environment | Behavior |
|-------------|----------|
| GUI (`gui.execute`) | New tab in the GUI |
| Headless (`--no-gui`) | Save to file |
| Direct run, no `fname` | `plt.show()` (popup window) |

Use `from zmlx.ui.pyqt import QtWidgets, QtGui, QtCore` instead of importing PyQt directly.

## API stability

**zmlx is a foundational library** — `zmlx/__init__.py` defines the public API.

- **Additive only**: new params (with defaults), new functions. Never remove/rename/change signatures.
- **Small changes**: 1–2 files at a time, then test.

## Anti-patterns

- **Modify** C++ kernel (`../../zml/`) — explain what's needed, author will handle
- **Delete** test scripts — add new ones
- **Import** from `zml` — use `zmlx`
- **Add** deps to `zmlx/exts/`

## Coding style

- **Imports**: stdlib → typing → zmlx → local. Warn via `import zmlx.alg.sys as warnings`.
- **Docstrings**: Google-style, Chinese module docs. `"""简述。\n\nArgs:\n    p: 说明\n\nReturns:\n    值\n"""`
- **Signatures**: `fn(P, T)` pressure-first, SI units. `Optional[X]` for nullable. `*` for keyword-only.
- **Validation**: `if x <= 0: raise ValueError(...)` — not `assert` (stripped by `-O`).
- **Naming**: `snake_case` functions, `PascalCase` classes, `_private` modules.
- **Gotchas**: No Chinese in install path; `zmlx/config/` and `zmlx/base/` are deprecated.
