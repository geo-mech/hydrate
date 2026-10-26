# AGENTS.md

**`zmlx/ui/extra_setups/`** 的规范：**「必须加载」的界面装配住在哪里**。

⚠️ 本文件只回答一件事：**某段代码该不该放进 `extra_setups/`，放进来之后怎么写、按什么顺序执行**。
控件的写法见 [`../widgets/AGENTS.md`](../widgets/AGENTS.md)；插件的规范见
[`../plugins/AGENTS.md`](../plugins/AGENTS.md)；本文件**不重复**这两份。

上承 `projects/zml/AGENTS.md` 与 [`../AGENTS.md`](../AGENTS.md)；冲突时以更具体者为准
（本文件 > `../AGENTS.md` > `projects/zml/AGENTS.md` > 仓库根 `AGENTS.md`）。

## 0. 存在的意义

`main.py` 里的 `MainWindow` 是界面骨架：菜单栏、标签容器、命令表、控制台、状态栏。
**骨架之外的「装配」不该都堆进那个文件**，否则它会长成一块没人敢动的巨石。

`extra_setups/` 就是这类装配的落脚处：

> **它的意义 = 让 `main.py` 只保留「骨架」，把「往骨架上挂东西」挪出来。**

两个小节各有一个「巨石」，`extra_setups/` 的价值就是**不让它们变胖**：

| 巨石 | 现在多大 | `extra_setups/` 从中拿走的是什么 |
|---|---|---|
| `main.py` | 2760 行 | 各类**必须加载**的菜单 / 命令注册（授权查询、用户管理、架构页……） |
| `MainWindow.__init_actions` | 约 470 行、32 次 `add_action`（30 个菜单项 + 2 份分隔符） | 同上 —— 本该是骨架自带的「文件 / 操作 / 显示」才留在那里 |

## 1. 与插件：**同一类东西，只差一个「能不能关」**

⚠️⚠️ **两者的运行环境几乎完全一样**，这一点很容易被误解，先说清楚：

| | `extra_setups/` | `plugins/` |
|---|---|---|
| 什么时候跑 | 界面启动时 | 界面启动时 |
| 在哪个线程跑 | **控制台（console）线程** | **控制台（console）线程** |
| 谁来调 | `main.py` 的 `__console_kernel` → `extra_setups.setup_ui()` | 同一个 `__console_kernel` → `plugins.load_all()` |
| 怎么动界面 | 一律 `gui.xxx(...)`（派发到 GUI 线程） | 一律 `gui.xxx(...)`（派发到 GUI 线程） |
| **能不能关** | ❌ **不能** —— 必加载 | ✅ 能（「设置 → 插件」里勾掉） |
| 文件放哪 | 本目录 | `plugins/builtin/` 或 `scen/<包>/zml_plugin.py` |

**唯一的判据**（也是唯一的分界线）：

> **关掉它，软件还能不能正常用？**
> 不能 → `extra_setups/`；能 → 插件。

⚠️ 已经有几处搬迁印证了这条判据，**不要把它们再挪回去**：

| 功能 | 曾放在 | 现在 | 理由 |
|---|---|---|---|
| 用户管理 | `plugins/user_admin.py` | 本目录 `user_admin.py` | 授权查询与修改是**产品功能**，不该让用户关掉 |
| 数据编辑器（7 种文件类型） | 本目录 `editors.py` | `plugins/builtin/editors.py` 插件 | 「文件 → 打开」少了这些还能用，属于可关闭的扩展 |
| 两个彩蛋游戏 | `plugins/builtin/` | `scen/easter_eggs/` 插件 | 彩蛋显然可关掉 |
| Admin 功能、运行环境 | 本目录 | `plugins/builtin/` | 开发 / 调试用的入口，不该常驻 |

⚠️ **判据不是「这个功能重要不重要」，而是「关掉它软件还能不能正常用」。**
「重要」是主观判断，会随人、随时变；「关掉还能不能用」是可检验的。

## 2. 放进来之后怎么写

标准形状（与 `plugins/` 的插件**几乎一样**，只是没有 `# **` 元数据、也不用自己调）：

```python
# zmlx/ui/extra_setups/xxx.py
"""一句话说明挂的是什么 + 挂在哪一级菜单.

为什么在 extra_setups 而不是 plugins：<用 §1 的判据回答>
"""

from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():
    """注册命令 + 挂菜单（由 ``extra_setups/__init__.py`` 调用）."""
    from zmlx.ui import gui          # ⚠️ 函数体内 import：避免导入期就拉起 Qt

    gui.add_func('show_xxx', show_xxx)     # 命令
    gui.add_action(menu='帮助', text='xxx', slot=show_xxx)   # 菜单项
```

四条硬性要求：

1. **必须带 `@execute_once(file=__file__)`**：`extra_setups/__init__.py` 的 `setup_ui()`
   本身带装饰器，但**模块级函数也要带** —— 它可能被别处（如「临时加载」插件、直接运行本
   文件自测）重复调用，重复 `add_action` 会挂出两个菜单项。
2. **导入放在函数体内**：本目录模块由 `extra_setups/__init__.py` 延迟导入，但**别在模块顶层
   `from zmlx.ui import gui`** 之后又调注册 —— 顶层只允许 docstring / import / 定义。
   ⚠️ 无头模式下 `import zmlx.ui.*` 可能失败，重活一律推迟到 `setup_ui()` 里。
3. **模块顶层什么都别做**：它不像插件那样被 `exec`，而是被 **import** —— 顶层的每一条语句
   都会在导入时执行，等于「导入即注册」，那是导入期副作用。
4. **控件本体不在这里**：控件在 `ui/tabs/` 或 `ui/widgets/`；本目录只做「注册 + 挂菜单」
   （与 `plugins/` 的「只有入口」型完全同构）。

### 必须登记到 `__init__.py`

新增一个 `extra_setups/xxx.py` 之后，**必须**在 [`__init__.py`](__init__.py) 里按现有
`try/except` 风格加一段调用：

```python
try:
    from zmlx.ui.extra_setups.xxx import setup_ui
    setup_ui()
except Exception as err:
    print(f"Error when setup xxx: {err}")
```

⚠️ **每个都单独 `try`**：一个 setup 挂不上（缺可选依赖、控件导入失败）不能让其它 setup 跟着
垮 —— 这也是本目录所有调用点都写成 `try/except + print` 的原因。

⚠️ **不需要**（也不该）在任何 `__init__.py` 里转发本目录的**公开名字** —— 那是「公共 API」，
与本目录的用途无关，见 [`../AGENTS.md`](../AGENTS.md) §1。

## 3. 启动顺序：**顺序是契约，写在 `main.py` 里**

⚠️⚠️ 下面这条调用链在 [`../../ui/main.py`](../main.py) 的 `__console_kernel` 里，
**不要把它搬进 `extra_setups/`**：它是 `execute()` 的**顺序契约**，与 `MainWindow` 的构造
时机强耦合（`extra_setups` 能挂菜单，正是因为 `MainWindow` 已经构造完、`gui` 已接好）。

```
execute()
 └─ win = MainWindow()          # 骨架：菜单栏 / 标签容器 / console / 状态栏 + __init_actions
    __on_init(win)              # sys.stdout 接管、gui.set(api)、恢复输出历史
    win.show()
    __on_show(win)              # 窗口尺寸、样式表
    win.get_console().start_func(__console_kernel)     # ← 以下都在 console 线程
        ├─ __add_code_history()
        ├─ extra_setups.setup_ui()      # ★ 本目录：必加载的装配
        ├─ plugins.load_all()          # ★ 可禁用的扩展（逐条跳过禁用项）
        │    ⚠️ 外层还包着一个全局开关：`app_data.get('run_plugins',
        │       app_data.get('run_setup', True))` —— **默认执行**；
        │       `run_plugins` 是新名，`run_setup` 是旧名（2027-10-22 删）
        ├─ __check()                    # 环境自检（PyQt5 / 中文安装路径）
        ├─ __restore_tabs()             # 按 gui_restore 重放上次的标签页
        └─ code()                       # 用户传进来的脚本
```

**三条必须记住的顺序约束**：

1. **`extra_setups` 先于 `plugins`**。两者都会 `gui.add_func` / `gui.add_action`；本目录是
   **必加载**的，先跑它，保证核心命令存在；插件随后跑，装不上/被禁用都不影响核心。
   ⚠️ **本目录内部也有顺序要求**：`plugin_placeholders` 必须**第一个**跑 —— 它挂的是插件命令
   的**占位**（`gui.get_vtk_view` / `gui.show_style_sheet` …），插件启用后要用同名
   `gui.add_func` **覆盖**它们；顺序反了，占位就会顶掉插件。
   ⚠️ **这里的「先」只对** `gui.add_func` **有意义**：它是两条各自的 `exec` 语句，顺序
   由上面的调用链决定。至于 `gui.add_action`（菜单项），`gui` 缓冲区在 GUI 线程里执行它，
   而 `extra_setups` 与插件是在**同一个**内核线程里**顺序**提交这些调用的 —— 所以**不跨
   线程竞争**。（2026-10-22 查证：`MainWindow` 在 GUI 线程构造，此时内核还没启动。）
2. **两者都先于 `__restore_tabs()`**。恢复标签页时会 `exec` 形如
   `gui.open_seepage('...')` / `gui.show_check_count_view()` 的**存量字符串** ——
   命令必须已经注册好，否则重放会失败（这是「命令名一旦发布不能改」的根本原因：
   改个名，老用户的标签页就恢复不了）。
3. **`extra_setups` 在 `MainWindow` 构造之后**。`__init_actions`（骨架自带的「文件 / 操作 /
   显示」菜单）先执行，本目录**只负责往菜单里填条目**，决定不了菜单/子菜单本身的位置。
   ⚠️ 例如「帮助 → 用户」「帮助 → 查询」两个子菜单的**位置**由 `main.py` 的两行 `get_menu`
   决定，本目录只往里面加条目 —— 所以「管理」要在 `user_admin` 里排在 `license_query`
   之前，才能保证条目顺序正确。

## 4. 加一个菜单项之前：三问

1. **它必须加载吗？** 按 §1 的判据。能关 → 去做插件，别放这里。
2. **命令名会不会与 `MainWindow` 的公开方法撞车？** `__init_gui_api` 会把主窗口的
   **所有公开方法自动注册**进命令表，同名会把那个方法悄悄顶掉。
3. **命令名能不能以后改？** 不能 —— 标签页状态里存的就是 `gui.show_xxx()` 这串原文，
   重启时按原文重放。要改就得像 `license_query.py` 末尾那样**留旧名别名**。

### ⚠️ 什么**不**该进来

本目录是「**装配层**」（挂菜单、注册命令），**不是「GUI 辅助函数」的杂物间**。
判据很朴素：**它有没有往界面上挂东西 / 注册命令？**

| 想迁的东西 | 放哪 | 理由 |
|---|---|---|
| 挂菜单、注册 `gui.xxx` 命令、往已有控件里加东西 | ✅ **本目录** | 这就是装配 |
| **构造 / 查询方法**（返回一个 widget，例如 `get_widget` / `get_figure_widget` / `get_plot_widget`） | ❌ 留在 `MainWindow` | 它是**骨架的能力**，`gui.get_widget` 也因此可用 |
| **只服务某个插件、且依赖可选库**的方法 | ❌ 搬进**那个插件** | 例：`get_vtk_view`（依赖 `pyvistaqt`）2026-10-22 由 `MainWindow` 搬进 `plugins/builtin/vtk_view.py`。⚠️ 它的**占位**（只打印「请先启用 XXX 插件」）放在本目录的 [`plugin_placeholders.py`](plugin_placeholders.py)，插件启用后靠 `gui.add_func` **后写覆盖**它 —— 这样命令名不会消失、还能给出可操作提示，详见 [`../plugins/AGENTS.md`](../plugins/AGENTS.md) §2 |
| 用户可下开关的扩展 | ❌ 插件 | 见 §1 判据 |

⚠️ **一个必须先想清楚的陷阱**：`MainWindow` 的公开方法会**自动**变成 `gui.xxx`（见
`__init_gui_api`）。所以把一个方法搬出 `MainWindow` 时，**它的命令名会一起消失** ——
必须在新的家显式 `gui.add_func('旧命令名', 新函数)`，否则原来的调用方（尤其那些
**默认不加载、容易被漏测**的插件）会报 `gui function <xxx> not found`。

⚠️ 反过来说：**「看着像 GUI 辅助函数」不是搬进本目录的理由**。硬塞进来会让本目录从
「装配层」退化成杂物间，`main.py` 的减重也换不来什么（那些方法往往只有几行）。

## 5. 现状（5 个文件）

| 文件 | 挂的是什么 | 为什么是「必加载」 |
|---|---|---|
| `user_admin.py` | 帮助 → 用户 → 管理 | 授权查询与修改是**产品功能**，不该被用户关掉 |
| `license_query.py` | 帮助 → 查询 → 授权记录 / 反馈记录 | 同上：登录与反馈记录是产品功能 |
| `architecture.py` | 帮助 → 架构 | 代码库入门页，属文档类产品功能 |
| `plugin_placeholders.py` | **15 条插件命令的占位**（`gui.get_vtk_view` / `gui.show_style_sheet` / …） | 必须**先于插件**挂上：插件启用后要用同名 `gui.add_func` 覆盖它。⚠️ 在 `__init__.py` 里**排第一位** |
| `__init__.py` | 编排：逐个 `try` 调用上面四个 | —— |

⚠️ `architecture.py` 有 2969 行（内含大段图文），且**在模块顶层就 import Qt 控件** ——
所以 `__init__.py` 里对它用 `getattr(module, 'provide_gui_setup', None)` **类型探测**式调用，
取不到就安静跳过，不会带崩整个 `setup_ui()`。新加入的模块**不要**照抄这个例外，
那是为「可选 Qt / 无头环境」准备的（详见该文件 `provide_gui_setup` 的 docstring）。

⚠️ 本目录**曾经还有** `editors.py`（数据编辑器文件类型注册）—— 2026-10-22 已随「数据编辑器」
整体移入插件 [`zmlx/ui/plugins/builtin/editors.py`](../plugins/builtin/editors.py)，因为
「关掉它，软件还能正常用」（只是少了编辑那几种文件的能力）。这是**按 §1 判据做的搬迁**，
不是失误。（中途它曾在 `zmlx/scen/editors/` 里住过半天，同日取消、控件退回
`ui/widgets/editors/`、装配合成那一个文件。）

## 6. 验收

```bash
# 1. 本目录文件数（应为 5：__init__ + 4 个 setup）
ls zmlx/ui/extra_setups/*.py | wc -l

# 2. 编排表里每个模块都被登记了（漏登记 = 静默不生效）
grep -c 'from zmlx.ui.extra_setups' zmlx/ui/extra_setups/__init__.py

# 3. 无头环境不炸（顶层不 import Qt 重活的判据）
python -c "from zmlx.ui.extra_setups import setup_ui; print('ok')"
```

⚠️ 涉及界面的自测（真的把菜单挂上去看）要用系统 WinPython，见 `projects/zml/AGENTS.md`。
