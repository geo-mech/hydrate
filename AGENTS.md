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
- **Version numbers**: `pyproject.toml` and `zmlx/__init__.py` (`__version__`) must always
  agree — `zmlx` is not pip-installed, so `importlib.metadata.version('IggHydrate')` returns
  nothing and callers rely on `__version__`.
- **Version numbering scheme**: in `x.y.z`, the **patch number z increments with ordinary
  development commits** — it orders work in progress and is not a release marker. A **minor
  version bump (y + 1, z reset to 0)** is a release: that `x.y.0` is the version users receive.
  Consequence for `CHANGELOG.md`: patch-level entries record development history, and the
  accumulated patch entries are consolidated into one summary under the new `x.y.0` heading at
  release time.
- **`CHANGELOG.md`** (`zmlx/data/CHANGELOG.md`) is written per commit; published release notes
  are consolidated from it at release time.
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

---

# 工作流

以下四个工作流原先在 `.claude/commands/`（已删除），现以此为唯一来源。

### Git 约定（重要）

- **永远不要执行 `git push`**，只做本地 `commit`（及必要的 `add` / `reset --soft` / `restore`）。
- 推送由用户手动完成；回复中需提醒「尚未推送」。

---

## 0. 追加提交（amend）

当用户说「**追加提交**」（或「追加到当前提交」「并进上一个提交」）时，**不要走「1. 提交」的完整流程**：

**判据：是否存在尚未推送的提交？**

```bash
git log origin/master..HEAD --oneline     # 有输出 = 存在未推送提交
```

| 情况 | 怎么做 |
|---|---|
| **有**未推送提交 | **追加到最近那个**：`git add -A` + `git commit --amend`，**不升版本号**、**不新增 CHANGELOG 条目**（若本次改动值得记，**补进那个提交对应的 CHANGELOG 条目**即可） |
| **没有**未推送提交 | 没有可追加的目标 ⇒ **退回「1. 提交」的完整流程**（升版本号 + 新增 CHANGELOG 条目） |

⚠️ **为什么这样分**：未推送的提交还没到别人手里，追加进去等于「这次提交还没定稿」，不必为一个
中间状态多出一个小版本号（否则一天能刷出 v1.9.4 ~ v1.9.9 六个版本，CHANGELOG 反而读不出东西）。
一旦推送出去就是公开历史，只能新增提交、不能再改。

⚠️⚠️ **追加时的两个硬性要求**：

1. **提交描述要一起更新** —— `--amend` 会沿用旧描述，必须把本次改动补进去（照旧用
   `== 分类标题 ==` + 条目的格式）。⚠️ **Windows PowerShell 里不要用 `-m "多行"`
   （实测会把换行吃掉，标题与正文挤成一行）**，一律写进临时文件再用 `-F <文件>`：
   ```bash
   git commit --amend -F /path/to/msg.txt
   ```
2. **`--amend` 会改掉提交哈希**。改完用 `git log --oneline -1` 看一眼标题是否干净、
   `git log -1 --format=%B` 确认正文换行还在。

⚠️ **绝对不要 `amend` 已推送的提交**（会与远端历史分叉）。不确定时先跑一次
`git log origin/master..HEAD --oneline` 确认目标提交确实未推送。

---

## 1. 提交（commit）

当用户要求「提交」时，执行以下操作：

⚠️ **先看一眼有没有未推送的提交**：如果用户只是说「提交」而**已有未推送提交**，仍按本节
完整流程走（新版本 + 新条目）—— 只有用户明确说「**追加**」时才走上一节。

1. **读取未提交修改**：运行 `git diff --stat HEAD` 和 `git status`，阅读实际改动内容，
   用 1-2 句话总结本次修改的核心内容

2. **升级版本号**：读取 `pyproject.toml`，将最小版本号（z）加 1（如 1.7.1 → 1.7.2）；
   ⚠️ **同时**把 `zmlx/__init__.py` 顶部的 `__version__` 改成同一个新版本号 ——
   两处必须始终一致。`zmlx` 没有 dist-info（不是 pip 安装的），
   `importlib.metadata.version('IggHydrate')` 什么也读不到，程序和外部调用者只能靠
   `__version__` 判断自己面对的是哪个版本，它一旦掉队就会对外撒谎。
   （因此本文件的「版本号」永远指 `pyproject.toml` 的那个，`__version__` 只是它的影子。）

3. **更新 CHANGELOG**：改 `zmlx/data/CHANGELOG.md`（**唯一的** CHANGELOG，仓库根目录
   那份已删除）。**每个版本都在顶部新增一条自己的条目**，标题就是这次升级后的新版本号 ——
   每个版本**只写一小句话**（一句话说清这个版本改了什么即可，不要展开成分类列表）：
   `## v新版本 (日期)` + 一行说明，下面按需列要点。
   ⚠️ **不要把多个版本并进同一条**（即便都在同一天，也各写各的；标题里的版本号必须与
   `pyproject.toml` 升级后的版本一致）—— 版本号对不上改动，CHANGELOG 就失去意义了。
   ⚠️ 只有**小版本发布**（x.y.0，见「3. 公开发布」）才把补丁版本收拢成一条汇总；
   写法照 `v1.9.0` / `v1.8.0` / `v1.7.0`。
   ⚠️ **已经发布的小版本条目（`v1.9.0` / `v1.8.0` / `v1.7.0`）此后一律不再修改**：当前
   周期的补丁汇总暂记在**本周期最早的那条条目**里（现在是 `v1.9.21`），等下一个 x.y.0
   发布时整体转移过去 —— 别往老条目里塞新内容。

4. **同步 ReadMe**：检查 `git diff --stat` 中涉及的子包和 `zmlx/` 核心，如果改动较大，
   更新 `zmlx/ReadMe.md` 和对应子包的 `ReadMe.md`。
   ⚠️⚠️ **两份 ReadMe 必须成对修改**：`README.md`（仓库根目录）与
   `zmlx/data/README.md`（随 wheel 发布的那一份，UI 的「帮助 → ReadMe」读的就是它）。
   **任一方向都要同步** —— 改了根目录那份就覆盖 data 版，改了 data 版就覆盖根目录那份；
   两份内容应**逐字节相同**。改完用一条命令确认（哈希一致才算同步好了）：

   ```bash
   # 两份的 SHA-256 必须相同；不同就是漏同步了
   git hash-object projects/zml/README.md projects/zml/zmlx/data/README.md
   ```

   ⚠️ **为什么强调"成对"**：原先只说「改了根目录那份要覆盖 data 版」（单向），且把这件事
   描述成「极少改」。结果两份**真的漂了**（2026-10-10 核对发现：data 版多出整节「隐私声明」、
   根版另有更重的加粗强调，措辞也有出入 `在离线环境下使用` vs `离线使用`）—— 直到有人
   主动比对才发现。**只朝一个方向写规则，反方向就会漏**。原先由
   `zmlx/ui/data/md_sync.py` 在运行时自动复制，该模块已删除（三份文档里只剩 README
   需要同步），改由 agent 手动复制 —— 手动就意味着**必须每份都记得**。

5. **生成提交描述**：中文，结构化，基于第 1 步的总结展开

6. `git add -A && git commit`

⚠️ **提交时不跑 demo 批量测试**：本流程只有上面 6 步，「顺手验证一下」不在其中。

---

## 2. 合并未推送提交（squash）

当用户要求「合并」（意图为压缩未推送的提交）时：

1. `git log origin/master..HEAD --oneline` 看未推送提交，`git diff origin/master..HEAD --stat` 看变更
2. 读 `origin/master` 上 `pyproject.toml` 的版本号作基准，小版本号 **+1** 作为合并后版本号
   （如基准 1.7.1 → 1.7.2，**不是**累加中间各次增量）
3. `git reset --soft origin/master`，把所有提交压回暂存区
4. 更新 `pyproject.toml`、`zmlx/__init__.py` 的 `__version__` 与 `zmlx/data/CHANGELOG.md`
   的版本号（三处保持一致）
5. `git commit`，描述格式：版本号 + 简短描述，空行，然后 `== 分类标题 ==`
   （核心重构 / bug修复 / demo / 文档 / 配置）+ 各项简短列表。

---

## 3. 公开发布（release）

当用户要求「发布」时，执行以下操作：

1. **升级中间版本号**：`pyproject.toml` 中 y 加 1，z 重置为 0（如 1.6.33 → 1.7.0）；
   `zmlx/__init__.py` 的 `__version__` 同步改为该新版本号（同「1. 提交」第 2 步）

2. **整理 CHANGELOG**（`zmlx/data/CHANGELOG.md`）：把**当前周期**的 z 级条目（`v1.9.1` ~
   `v1.9.N`，连同它们的补丁汇总）**整体转移**进新的 x.y.0 条目 —— 收拢成一条汇总，与其它
   历史条目保持同样的密度（**每个版本一小句话**）；范例：`v1.9.0` 条目里的「以下要点汇总
   v1.8.1 ~ v1.8.37」。⚠️ 转移后那些 z 级条目即由这条汇总取代，**已经定稿的小版本条目
   不再改动**。
3. `git add -A && git commit`

---

## 4. 批量测试（test）

⚠️ **仅当用户明确要求「测试」/「跑 demo」时执行**：长耗时（十几分钟到几十分钟），
提交 / 合并 / 发布都**不包含**它，不要自行触发。

```bash
python zmlx/demos/test_all_demos.py [--jobs N] [--timeout N]
```

默认 `--jobs` = CPU 核心数、`--timeout 60`；「快速测试」→ `--timeout 30`，
「深度/详细/仔细测试」→ `--timeout 500`。跑完读 `test_report.log`，汇报通过 / 超时 / 失败 / 错误。

