# AGENTS.md

Guidance for AI agents working in `projects/zml/` — the Python side (IGG-Hydrate, package
`IggHydrate`, `import zmlx`). For the C++ kernel (`zml/`), see the repository-root `AGENTS.md`.

## Project overview

**IGG-Hydrate** is a reservoir multi-field coupling simulator (Thermal-Hydraulic-Mechanical-Chemical).

## Public API and release compatibility

This package is published as **IGG-Hydrate** (<https://gitee.com/geomech/hydrate>), so treat
everything here as **publicly shipped code**:

- **API stability**: `zmlx/__init__.py` defines the public API. Changes must be *additive*
  (new params with defaults, new functions). Never remove, rename, or change the meaning of an
  existing signature. Renames need a forwarding shim that emits `DeprecationWarning` and states a
  definite removal date (convention: one year), see the "包名" section below.
- **Keep this file public-facing**: durable engineering guidance only — no personal notes,
  scratch reasoning, or pointers to files that do not ship in this directory.

## Architecture

Strict layering — upper layers may use lower ones, never the reverse:

| Layer | Directory | Purpose |
|---|---|---|
| 5 | `zmlx/scen/` | Application scenarios |
| 4 | `zmlx/tfc/` | Physics engine — `Seepage.iterate()` |
| 3 | `zmlx/ui/`, `zmlx/plt/`, `zmlx/fig/` | GUI / plotting |
| 2 | `zmlx/fluids/`, `zmlx/reactions/` | Physics models — see `fluid/ReadMe.md` |
| 1 | `zmlx/exts/` | DLL bindings — **thin**, one export per function |

Also: `zmlx/demos/` (runnable examples — learn the API here), `zmlx/fem/`, `zmlx/meshes/`,
`zmlx/geometries/`, `zmlx/io/`, `zmlx/algs/`, `zmlx/krs/`, `zmlx/utils/`.

- **`Seepage`** = central data structure (cells, faces, fluids, iteration state)
- **Dependency**: `system/` → `exts/` → everything else

## GUI mode

### Entry point pattern

`gui.execute(main, close_after_done=False)` **only** inside `if __name__ == '__main__'` —
never inside a function (it nests and behaves unpredictably). `main()` runs on the GUI thread,
so use `gui.break_point()` / `gui.progress(...)` inside long loops (both no-op headless).

### `gui.*` functions (auto no-op in headless mode)

| Function | Purpose |
|----------|---------|
| `gui.break_point()` | Pause/stop checkpoint |
| `gui.progress(label, range, value)` | Progress bar |
| `gui.information(title, text)` | Info dialog |
| `gui.question(text)` | Yes/no dialog |
| `gui.show_attrs(**attrs)` | Dynamic variable display |
| `gui.in_dark_mode()` | Check dark mode (GUI only) |

### Calling registered commands: only `gui.xxx(...)`

To call a function in the GUI command table, **always** write `gui.xxx(...)` — never
`gui.get().xxx()`:

```python
gui.list_all()                 # ✅  __getattr__ -> Agent -> command('list_all')
gui.get_func('plot')           # ✅
gui.get().list_all()           # ❌  bypasses GuiBuffer's dispatch layer
```

The attribute access *is* the contract: `GuiBuffer.__getattr__` turns `gui.<name>` into
`Agent` → `command('<name>', ...)`, so a missing command raises `RuntimeError` at one single
place and a cross-thread call is moved to the GUI thread automatically. `gui.get()` returns the
`GuiApi` instance; calling methods on it skips that layer — inside the GUI thread you cannot tell
the difference, from a worker thread you lose the only thread guarantee there is. Rule of thumb:
if the name appears in `gui.list_all()`, call it as `gui.<name>(...)`. See `zmlx/ui/AGENTS.md`
§6.2 and the module docstring of `zmlx/ui/gui_buffer.py`.

### Matplotlib plotting: `zmlx.ui.plot`

Produce figures via a callback + `zmlx.ui.plot(on_figure, caption="...")` (the callback gets a
`fig`; add axes to it). It auto-adapts: GUI → new tab, headless → saved file, direct run without
`fname` → `plt.show()`. Import Qt via `from zmlx.ui.pyqt import ...`, never `from PyQt6 import ...`.

## API stability

**zmlx is a foundational library** — `zmlx/__init__.py` defines the public API.

- **Additive only**: new params (with defaults), new functions. Never remove/rename/change signatures.
- **Small changes**: 1–2 files at a time, then test.

## Anti-patterns

- **Delete** test scripts — add new ones
- **Import** from `zml` — use `zmlx`
- **Add** deps to `zmlx/exts/`

## Coding style

- **Imports**: stdlib → typing → zmlx → local.
- **Docstrings**: Google-style, Chinese module docs. `"""简述。\n\nArgs:\n    p: 说明\n\nReturns:\n    值\n"""`
- **Signatures**: `fn(P, T)` pressure-first, SI units. `Optional[X]` for nullable. `*` for keyword-only.
- **Validation**: `if x <= 0: raise ValueError(...)` — not `assert` (stripped by `-O`).
- **Naming**: `snake_case` functions, `PascalCase` classes, `_private` modules.
- **Gotchas**: No Chinese in install path; `zmlx/config/` and `zmlx/base/` are deprecated.

### 包名：只有「内容集合」才用复数

⚠️ **不要一看到单数包名就想改成复数。** 判据是**这个包是"装东西的容器"，还是"架构里的一层"**：

| 类型 | 判据 | 例子 | 用法 |
|---|---|---|---|
| **内容集合** | 包里是**同类事物的多个实例** | `fluids`（一堆流体）、`reactions`（一堆反应）、`geometries`、`meshes`、`demos`、`utils`、`ui/widgets` | ✅ **用复数** |
| **架构分层 / 缩写** | 它是**层级坐标**，或本身就是**约定俗成的缩写** | `ui`、`io`、`exts`、`tfc`、`fem`、`fig`、`plt`、`pg`、`scen`、`ptree`、`base`、`config`、`data`、`system`、`matlab` | ❌ **保持原样** |

**为什么分层名/缩写不动**：

1. **缩写的复数形式往往认不出来** —— `scen` 是 `scenario` 的缩写，改成 `scens` 是个**英语里不存在、编程圈也无先例**的词，比原名更难懂。（`algs` 是例外：`algorithms → algs` 在算法库里有惯例。）
2. **层级名用单数/缩写是通行做法** —— 没人会把 `ui` / `io` / `exts` / `tfc` 改成复数；单挑其中一个改反而破坏一致性。
3. **收益小于代价** —— 这类包往往文件多（`scen/` 有 131 个），改名要动一大片加全套垫片，而外部使用极少。

⚠️ **要改就整批改，不要只挑一个。** 只把 `scen` 改成 `scens`、而 `exts`/`tfc`/`ui` 保持单数，是**最差的结果** —— 既不统一，又多了个认不出的名字。

⚠️ **改名必须留兼容垫片**：旧路径保留为转发层，**导入即发 `DeprecationWarning`**，
并写明**确定的删除日期**（惯例：改名之日起**一年**，如 2026-10-16 改名 → 2027-10-16 删除）。
垫片用「模块级 shim + 子包 shim + 包级 PEP 562 `__getattr__` 惰性转发」三层齐备，
且 `__init__.py` **不可省略**（没有它旧包就不是包，所有老路径全失效）。

⚠️⚠️ **删除任何"已弃用"的包之前，必须连外部工作区一起搜** ——
**「本仓没人 import」不等于「没人用」**。本项目曾因此误删 `ui/GuiBuffer.py` 与 `zmlx/demo`，
事后核对 `igg-hydrate-works` 下 **12 个项目、432 条导入语句**才发现有**外部引用**，只能恢复。
所以：① 搜范围要包含外部项目；② 改完用**基准提交反推全量清单**逐个验证，
而不是"看代码觉得没问题"（那样会漏掉别名、`get_path` 这类直接赋值、以及
`os.path.join(..., 'demo', ...)` 这种 import 检查看不见的**字面量路径**）。

### 警告：一律用 `zmlx.system.warn`，不用标准库 `warnings.warn`

⚠️ **本仓（`zmlx/`）内除 `zmlx/system/` 自己以外，发警告一律用**
:func:`zmlx.system.warn`，**不要**写 `warnings.warn(...)`，也**不要**再用
`import zmlx.algs.sys as warnings` 这种别名（那是历史写法，2026-10-17 已全量迁移完毕）。

```python
from zmlx.system import warn          # ✅

warn('``zmlx.alg`` 已弃用（2026-10-16）：…')
warn('参数越界，已改用默认值', UserWarning, stacklevel=2)
```

**为什么**

`zmlx.system.warn` 在 `warnings.warn` **之外多做一件事**：把这条警告**记到日志并保留标记**
（`log(tag=...)` → `app_data.add_tag_today`，同一标签**当天只记一次**）。于是作者能回答一个
光靠警告问不出来的问题 ——「**这个东西标了弃用，到底还有没有人在用**」：只有一条条
`DeprecationWarning` 飘过去，是看不出"该不该删"的；而"今天有没有被用到"是**可查的**。

⚠️ **「当天只记一次」是刻意的**：需求是「知道**是否**用过」，不是「用了多少次」。
所以不要为它另做计数机制 —— 去重正好就是需要的语义。

**范围与例外**（重要）

| 范围 | 做法 |
|---|---|
| `zmlx/` 下**除** `zmlx/system/` 以外 | ✅ **必须**用 `from zmlx.system import warn` |
| `zmlx/system/` 内部 | ❌ **不要**这么写 —— 它就是 `warn` 的定义处，自己导入自己会**循环导入**（依赖链 `_warn → _log → _app_data`，实测报 `partially initialized module`） |
| 需要 `warnings` 的**其它**能力（`simplefilter` / `catch_warnings` / `filterwarnings`） | 照常用 `import warnings` —— 本约定只管 **`warn`** |

**三条实操要点**

1. **导入必须在调用之前**。垫片常见写法是「先发警告、再转发」，所以 `from zmlx.system import warn`
   要放在模块**最上面的 import 区**（紧跟 docstring），不能跟着下面的转发 import 一起放 ——
   否则 `warn(...)` 运行时 `NameError`。2026-10-17 的迁移**真的踩过这个坑（297 个文件）**。
2. **`stacklevel` 语义不变**：`warn()` 内部是 `warnings.warn(..., stacklevel=stacklevel + 1)`，
   所以原来写 `stacklevel=2` 的地方**原样保留 2** 即可，警告位置与改造前完全一致。
3. **`warn()` 的默认 `category` 是 `None`**（= 普通 `UserWarning`），而 `warnings.warn` 默认是
   `UserWarning` —— 两者一致，不必特意传。弃用请显式传 `DeprecationWarning`。

⚠️ **改完自检**：用 AST 确认「每个文件的 `from zmlx.system import warn` 行号 < 第一处
`warn(` 调用行号」，别只用正则 —— 多行调用、别名、条件分支都会骗过正则。

