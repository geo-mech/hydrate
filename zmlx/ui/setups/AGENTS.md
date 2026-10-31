# AGENTS.md

**`zmlx/ui/setups/`** 的规范：**「必须加载」的界面装配住在哪里**。

⚠️ 本文件只回答一件事：**某段代码该不该放进 `setups/`，放进来之后怎么写、按什么顺序执行**。
控件的写法见 [`../widgets/AGENTS.md`](../widgets/AGENTS.md)；插件的规范见
[`../plugins/AGENTS.md`](../plugins/AGENTS.md)；本文件**不重复**这两份。

上承 `projects/zml/AGENTS.md` 与 [`../AGENTS.md`](../AGENTS.md)；冲突时以更具体者为准
（本文件 > `../AGENTS.md` > `projects/zml/AGENTS.md` > 仓库根 `AGENTS.md`）。

⚠️ **2026-10-31：本目录由 `zmlx/ui/extra_setups/` 改名为 `zmlx/ui/setups/`**（用户要求，**不留垫片**）。

- **为什么改**：`extra_` 是「额外」的意思，可这里是**必加载**的装配 —— 名字与实际语义
  相反，还被新手读成"可选的附加物"。`setups/` 与里面的 `setup_ui()` 对得上。
- **老路径 `zmlx.ui.extra_setups.*` 已不可用**（`ModuleNotFoundError`）。改名前核实过：
  全仓唯一的真实 import 是 `main.py` 的 `from zmlx.ui.extra_setups import setup_ui`，
  其余命中全是注释 / 文档字符串。

## 0. 存在的意义

`main.py` 里的 `MainWindow` 是界面骨架：菜单栏、标签容器、命令表、控制台、状态栏。
**骨架之外的「装配」不该都堆进那个文件**，否则它会长成一块没人敢动的巨石。

`setups/` 就是这类装配的落脚处：

> **它的意义 = 让 `main.py` 只保留「骨架」，把「往骨架上挂东西」挪出来。**

两个小节各有一个「巨石」，`setups/` 的价值就是**不让它们变胖**：

| 巨石 | 现在多大 | `setups/` 从中拿走的是什么 |
|---|---|---|
| `main.py` | 2760 行 | 各类**必须加载**的菜单 / 命令注册（插件命令的占位等） |
| `MainWindow.__init_actions` | 约 470 行、32 次 `add_action`（30 个菜单项 + 2 份分隔符） | 同上 —— 本该是骨架自带的「文件 / 操作 / 显示」才留在那里 |

## 1. 与插件：**同一类东西，只差一个「能不能关」**

⚠️⚠️ **两者的运行环境几乎完全一样**，这一点很容易被误解，先说清楚：

| | `setups/` | `plugins/` |
|---|---|---|
| 什么时候跑 | 界面启动时 | 界面启动时 |
| 在哪个线程跑 | **控制台（console）线程** | **控制台（console）线程** |
| 谁来调 | `main.py` 的 `__console_kernel` → `setups.setup_ui()` | 同一个 `__console_kernel` → `plugins.load_all()` |
| 怎么动界面 | 一律 `gui.xxx(...)`（派发到 GUI 线程） | 一律 `gui.xxx(...)`（派发到 GUI 线程） |
| **能不能关** | ❌ **不能** —— 必加载 | ✅ 能（「设置 → 插件」里勾掉） |
| 文件放哪 | 本目录 | `plugins/builtin/` 或 `scen/<包>/zml_plugin.py` |

**唯一的判据**（也是唯一的分界线）：

> **关掉它，软件还能不能正常用？**
> 不能 → `setups/`；能 → 插件。

⚠️ 已经有几处搬迁印证了这条判据，**不要把它们再挪回去**：

| 功能 | 曾放在 | 现在 | 理由 |
|---|---|---|---|
| 用户管理 | `plugins/user_admin.py` → 本目录 `user_admin.py` | **又回到** `plugins/builtin/user_admin.py`（2026-10-31） | ⚠️ **判据重新判过、结论反了**：关掉它软件照样能建模 / 求解 / 绘图，只是少了「按用户改授权」这个入口 ⇒ 可关闭的扩展。见下方专条 |
| 数据编辑器（7 种文件类型） | 本目录 `editors.py` | `plugins/builtin/editors.py` 插件 | 「文件 → 打开」少了这些还能用，属于可关闭的扩展 |
| 两个彩蛋游戏 | `plugins/builtin/` | `scen/easter_eggs/` 插件 | 彩蛋显然可关掉 |
| Admin 功能、运行环境 | 本目录 | `plugins/builtin/` | 开发 / 调试用的入口，不该常驻 |

⚠️ **「用户管理」这一条要读全**（2026-10-31）：它 2026-10-18 曾被判为「产品功能、不该让
用户关掉」而搬进来，2026-10-31 **按同一判据重判、结论相反** —— 关掉它，建模 / 求解 /
绘图一概不受影响（真正「关不掉」的是**登录与授权检查本身**，那在 `MainWindow` /
`tabs/license_register.py` / `widgets/license_button.py`，不在这两个目录里）。
搬迁时 `tabs/user_admin_view.py` 与 `license_query.py` 的内容先后并进那个插件文件，
两个原模块删除、**不留垫片**。
**这是判据的正常使用，不是反复无常**：判据留给人的是「关掉还能不能用」这个可检验的
问题，答案变了结论就变；但**别拿这一条当「搬来搬去都行」的先例** —— 再动它之前，
先按 §1 重新回答一遍那句话，并在提交信息里写清是哪一边变了。

⚠️ **判据不是「这个功能重要不重要」，而是「关掉它软件还能不能正常用」。**
「重要」是主观判断，会随人、随时变；「关掉还能不能用」是可检验的。

## 2. 放进来之后怎么写

标准形状（与 `plugins/` 的插件**几乎一样**，只是没有 `# **` 元数据、也不用自己调）：

```python
# zmlx/ui/setups/xxx.py
"""一句话说明挂的是什么 + 挂在哪一级菜单.

为什么在 setups 而不是 plugins：<用 §1 的判据回答>
"""

from zmlx.system import execute_once


@execute_once(file=__file__)
def setup_ui():
    """注册命令 + 挂菜单（由 ``setups/__init__.py`` 调用）."""
    from zmlx.ui import gui          # ⚠️ 函数体内 import：避免导入期就拉起 Qt

    gui.add_func('show_xxx', show_xxx)     # 命令
    gui.add_action(menu='帮助', text='xxx', slot=show_xxx)   # 菜单项
```

四条硬性要求：

1. **必须带 `@execute_once(file=__file__)`**：`setups/__init__.py` 的 `setup_ui()`
   本身带装饰器，但**模块级函数也要带** —— 它可能被别处（如「临时加载」插件、直接运行本
   文件自测）重复调用，重复 `add_action` 会挂出两个菜单项。
2. **导入放在函数体内**：本目录模块由 `setups/__init__.py` 延迟导入，但**别在模块顶层
   `from zmlx.ui import gui`** 之后又调注册 —— 顶层只允许 docstring / import / 定义。
   ⚠️ 无头模式下 `import zmlx.ui.*` 可能失败，重活一律推迟到 `setup_ui()` 里。
3. **模块顶层什么都别做**：它不像插件那样被 `exec`，而是被 **import** —— 顶层的每一条语句
   都会在导入时执行，等于「导入即注册」，那是导入期副作用。
4. **控件本体不在这里**：控件在 `ui/tabs/` 或 `ui/widgets/`；本目录只做「注册 + 挂菜单」
   （与 `plugins/` 的「只有入口」型完全同构）。

### 必须登记到 `__init__.py`

新增一个 `setups/xxx.py` 之后，**必须**在 [`__init__.py`](__init__.py) 里按现有
`try/except` 风格加一段调用：

```python
try:
    from zmlx.ui.setups.xxx import setup_ui
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
**不要把它搬进 `setups/`**：它是 `execute()` 的**顺序契约**，与 `MainWindow` 的构造
时机强耦合（`setups` 能挂菜单，正是因为 `MainWindow` 已经构造完、`gui` 已接好）。

```
execute()
 └─ win = MainWindow()          # 骨架：菜单栏 / 标签容器 / console / 状态栏 + __init_actions
    __on_init(win)              # sys.stdout 接管、gui.set(api)、恢复输出历史
    win.show()
    __on_show(win)              # 窗口尺寸、样式表
    win.get_console().start_func(__console_kernel)     # ← 以下都在 console 线程
        ├─ __add_code_history()
        ├─ setups.setup_ui()      # ★ 本目录：必加载的装配
        ├─ plugins.load_all()          # ★ 可禁用的扩展（逐条跳过禁用项）
        │    ⚠️ 外层还包着一个全局开关：`app_data.get('run_plugins',
        │       app_data.get('run_setup', True))` —— **默认执行**；
        │       `run_plugins` 是新名，`run_setup` 是旧名（2027-10-22 删）
        ├─ __check()                    # 环境自检（PyQt5 / 中文安装路径）
        ├─ __restore_tabs()             # 按 gui_restore 重放上次的标签页
        └─ code()                       # 用户传进来的脚本
```

**三条必须记住的顺序约束**：

1. **`setups` 先于 `plugins`**。两者都会 `gui.add_func` / `gui.add_action`；本目录是
   **必加载**的，先跑它，保证核心命令存在；插件随后跑，装不上/被禁用都不影响核心。
   ⚠️ **本目录内部也有顺序要求**：`plugin_placeholders` 必须**第一个**跑 —— 它挂的是插件命令
   的**占位**（`gui.get_vtk_view` / `gui.show_style_sheet` …），插件启用后要用同名
   `gui.add_func` **覆盖**它们；顺序反了，占位就会顶掉插件。
   ⚠️ **这里的「先」只对** `gui.add_func` **有意义**：它是两条各自的 `exec` 语句，顺序
   由上面的调用链决定。至于 `gui.add_action`（菜单项），`gui` 缓冲区在 GUI 线程里执行它，
   而 `setups` 与插件是在**同一个**内核线程里**顺序**提交这些调用的 —— 所以**不跨
   线程竞争**。（2026-10-22 查证：`MainWindow` 在 GUI 线程构造，此时内核还没启动。）
2. **两者都先于 `__restore_tabs()`**。恢复标签页时会 `exec` 形如
   `gui.open_seepage('...')` / `gui.show_check_count_view()` 的**存量字符串** ——
   命令必须已经注册好，否则重放会失败（这是「命令名一旦发布不能改」的根本原因：
   改个名，老用户的标签页就恢复不了）。
3. **`setups` 在 `MainWindow` 构造之后**。`__init_actions`（骨架自带的「文件 / 操作 /
   显示」菜单）先执行，本目录**只负责往菜单里填条目**，决定不了菜单/子菜单本身的位置。
   ⚠️ 例如「帮助 → 用户」「帮助 → 查询」两个子菜单的**位置**由 `main.py` 的两行 `get_menu`
   决定，本目录只往里面加条目。⚠️ 2026-10-31 起「用户」子菜单的三条条目**全部**在插件里
   （同一个 `setup_ui` 按顺序注册），本目录不再参与，也不再需要「谁先注册谁先排」那种约定。

## 4. 加一个菜单项之前：三问

1. **它必须加载吗？** 按 §1 的判据。能关 → 去做插件，别放这里。
2. **命令名会不会与 `MainWindow` 的公开方法撞车？** `__init_gui_api` 会把主窗口的
   **所有公开方法自动注册**进命令表，同名会把那个方法悄悄顶掉。
3. **命令名能不能以后改？** 不能 —— 标签页状态里存的就是 `gui.show_xxx()` 这串原文，
   重启时按原文重放。要改就得像 `plugins/builtin/user_admin.py` 末尾那样**留旧名别名**。

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

## 5. 现状（17 个文件）

| 文件 | 挂的是什么 | 为什么是「必加载」 |
|---|---|---|
| `message.py` | 显示 → 通知（`gui.show_messages` / `gui.add_message` / `gui.message`） | **基础设施**：`gui.add_message` 是 `main.py`（警告 / 异常）与 `plugins/_alg.py`（插件加载失败）的通用出口，做成插件就等于允许用户关掉「告警去哪看」 |
| `mem_view.py` | 显示 → 变量（`gui.show_memory`） | **必加载**：它往 `app_data` 里登记的 `app_data_edits` / `default_app_data_edit` 是**全局的变量编辑能力**，别的控件靠它决定「双击变量时用什么编辑器」—— 做成插件就等于允许用户关掉这一类交互 |
| `code_history_view.py` | 命令 `gui.show_code_history(folder, caption=None)`（**无菜单项**） | **必加载**：控制台的右键菜单「脚本运行历史」（`widgets/output_widget.py`）与代码编辑器的「编辑历史」（`widgets/code_edit.py`）都按**命令名**调它 —— 做成插件的话，关掉它这两个菜单项就变成「找不到命令」 |
| `output_history_view.py` | 命令 `gui.show_output_history()`（**无菜单项**），开「输出历史」标签页 | **必加载**：控制台右键菜单「输出历史」（`widgets/output_widget.py`）按**命令名**调它，与 `code_history_view.py` 是**同一条链** |
| `env_edit.py` | 设置 → 系统（`gui.show_env_edit`，`Ctrl+E`） | **必加载**：它改的是**全局配置**（界面标签位置 / 启动画面 / 控制台宽度…），改完对整个软件生效，属产品功能 —— 不该让用户在「设置 → 插件」里关掉；且带菜单项与快捷键，不是「只被打开成页面」的控件 |
| `string_table.py` | 命令 `gui.show_string_table(data, caption=None, data_columns=3)`（**无菜单项**，**返回那个 widget**） | **必加载**：它是给**插件 / scen / 脚本**用的通用出口 ——`plugins/builtin/admin_menu.py`（4 处）与 `scen/ai_assistant/action.py` 都按**命令名**调它；做成插件的话，那些调用方在插件关掉时就会「找不到命令」 |
| `plugin_list_edit.py` | 设置 → 插件（`gui.edit_setup_files`，action `setup_files`） | **必加载**：它是**插件机制的开关面板本身** —— 做成插件就成了「关掉『开关』」的循环，用户一取消勾选就再也找不回「启用 / 禁用插件」这个入口 |
| `readme_browser.py` | 帮助 → ReadMe（`gui.show_readme`，`F1`，**工具栏按钮**） | **必加载**：它是**欢迎页** —— `main.py` 的 `__on_show` 启动时按 `show_readme` 设置自动打开；做成插件会与「启动时显示欢迎页」这个设置互相打架。且带菜单项 / 快捷键 / 工具栏按钮，不是「只被打开成页面」的控件 |
| `license_register.py` | 帮助 → 登录（`gui.show_reg_tool`，action `reg`） | **必加载**：登录与授权检查是**软件本身**的一部分 —— 状态栏按钮（`widgets/license_button.py`）与 `exts/_lic.py` 的失败引导都按命令名调它；做成插件的话「关掉登录」既无意义又危险。⚠️ 名字是历史叫法：它开的是 `LicenseRegister`，不是 `RegTool` |
| `feedback_tool.py` | 帮助 → 反馈（`gui.show_feedback(text=None)`，action `feedback`，`is_enabled=not gui.is_running()`） | **必加载**：它是**出问题时的唯一出口** —— ReadMe 的「新建Issue」链接指向它，别处也用它预填现场信息；做成插件正好在最需要它时把它关掉。且带菜单项，不是「只被打开成页面」的控件 |
| `open_url.py` | 命令 `gui.open_url(url, caption=None, on_top=None, zoom_factor=None, icon=None)`（**无菜单项**） | **必加载**：它是 `zmlx.ui.alg.open_url`（全仓打开网址 / 本地 HTML 的**统一入口**）背后的**标签页实现** —— `alg.open_url` 在需要开标签页时正是调它；关掉它，「开网页」就只剩系统浏览器。⚠️ **与 `alg.open_url` 同名但两回事** |
| `text_in_tab.py` | 命令 `gui.show_text_in_tab(text, caption=None, on_top=None)`（**无菜单项**） | **必加载**：与 `string_table.py` 同类 —— 把一段内容丢进窗口看的**通用出口**，`scen/ai_assistant/action.py` 按**命令名**调它显示回答正文；做成插件的话，那个调用方在插件关掉时就会「找不到命令」。⚠️ 控件本体（`widgets/TextBrowser`）不在这里 |
| `gui_iter_edit.py` | 设置 → 迭代器（`gui.show_gui_iter`，action `gui_iter`） | **必加载**：这一页**不是用户点开的** —— `GuiIterator._plot_timing()` 在第一次绘图时直接 import 这个控件类并开标签页；做成插件的话那个自动化调用方根本不知道自己被关了。且带菜单项 |
| `about.py` | 帮助 → 关于（`gui.show_about`，`Ctrl+Shift+A`） | **必加载**：软件自身的版本 / 路径 / 登录状态页 —— 状态栏版本按钮（`widgets/version_button.py`）与 `readme_browser.py` 的右键菜单都按命令名调它；做成插件的话那两个入口就「找不到命令」。⚠️ 菜单的 slot 比命令多一步 `print(lic.desc)`（原样保留） |
| `check_license.py` | 命令 `gui.check_license()`（**无菜单项**，**已弃用**） | **必加载**：它是旧授权检查的**已弃用命令**，全仓无调用方，但原先是公开方法、自动注册成 `gui.check_license` —— 外部脚本可能在调；搬走时显式补了 `gui.add_func`，否则外部调用会从「一条弃用警告」变成「找不到命令」。⚠️ **不挂菜单、不加自动触发点**；弃用期到 **2027-10-05**，届时整体删除 |
| `plugin_placeholders.py` | **15 条插件命令的占位**（`gui.get_vtk_view` / `gui.show_style_sheet` / …） | 必须**先于插件**挂上：插件启用后要用同名 `gui.add_func` 覆盖它。⚠️ 在 `__init__.py` 里**排第一位** |
| `__init__.py` | 编排：逐个 `try` 调用上面一个 | —— |

⚠️ **本目录 2026-10-31 先缩到 1 个 setup、同日晚些又加入 `message.py`**：「帮助 → 用户」整块（管理 / 登录记录 /
反馈记录）与「帮助 → 架构」先后搬进插件 `plugins/builtin/`。**判据没有变** ——
问的一直是「关掉它，软件还能不能正常用」，而这三类东西的答案都是「能」。

⚠️ **`user_admin.py` 2026-10-31 已搬进插件** [`../plugins/builtin/user_admin.py`](../plugins/builtin/user_admin.py)
（默认加载；`tabs/user_admin_view.py` 与 `license_query.py` 的内容先后并进去，两个原模块
删除、**不留垫片**）：按 §1 判据重判后认为它属于「可关闭的扩展」。
⚠️ 连带的变化：它原先**靠"先注册先排"**才能在「用户」子菜单里排在 `license_query` 那几条
之前（见 §3 第 3 条）；合并进插件后，三条菜单项由**同一个** `setup_ui` 按顺序注册，
顺序恢复为「管理 → 登录记录 → 反馈记录」。这不影响功能。
⚠️ **`license_query.py` 2026-10-31 已并入同一个插件文件**（原模块删除、**不留垫片**）：
它里面只有两个 `show_xxx` 与 `setup_ui`，全都服务于「帮助 → 用户」这一个子菜单 ——
子菜单整块归了插件，装配代码也应当住在一起。四条命令名（含两个旧名别名）未变。

⚠️ **`architecture.py` 2026-10-31 已搬进插件** [`../plugins/builtin/architecture.py`](../plugins/builtin/architecture.py)
（默认加载）：它是纯文档页，关掉它软件照常可用 ⇒ 按 §1 判据属于「可关闭的扩展」。
⚠️ 这次搬迁顺带**删掉了一个例外**：原先 `__init__.py` 对它用
`getattr(module, 'provide_gui_setup', None)` **类型探测**式调用（因为它在模块顶层就
import Qt 控件）。现在它作为插件被 `exec`，顶层那句 import 只在**启用它时**才执行，
导入失败也只会让这一个插件记为 `Failed`，不影响 `setups`，所以不再需要那个例外 ——
**新加入的模块一律照常写 `setup_ui`**，不要照抄那个已消失的写法。

⚠️ 本目录**曾经还有** `editors.py`（数据编辑器文件类型注册）—— 2026-10-22 已随「数据编辑器」
整体移入插件 [`zmlx/ui/plugins/builtin/editors.py`](../plugins/builtin/editors.py)，因为
「关掉它，软件还能正常用」（只是少了编辑那几种文件的能力）。这是**按 §1 判据做的搬迁**，
不是失误。（中途它曾在 `zmlx/scen/editors/` 里住过半天，同日取消、控件退回
`ui/widgets/editors/`、装配合成那一个文件。）

## 6. 验收

```bash
# 1. 本目录文件数（应为 17：__init__ + 16 个 setup）
ls zmlx/ui/setups/*.py | wc -l

# 2. 编排表里每个模块都被登记了（漏登记 = 静默不生效）
grep -c 'from zmlx.ui.setups' zmlx/ui/setups/__init__.py

# 3. 无头环境不炸（顶层不 import Qt 重活的判据）
python -c "from zmlx.ui.setups import setup_ui; print('ok')"
```

⚠️ 涉及界面的自测（真的把菜单挂上去看）要用系统 WinPython，见 `projects/zml/AGENTS.md`。
