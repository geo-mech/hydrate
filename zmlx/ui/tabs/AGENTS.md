# AGENTS.md

**`zmlx/ui/tabs/`** 的规范补充页：本目录收「**顶层控件**」。

⚠️ **本目录的通用规范不在本文件里。** 控件骨架、命名与导入约定、右键菜单
（`context_actions` + `create_action`）、可选依赖的两种写法、`app_data` 的两套存储、
`refresh()` 的性能约束、线程生命周期契约、自测与验收 —— 一律沿用
[`../widgets/AGENTS.md`](../widgets/AGENTS.md)（那是全仓控件的唯一规范来源）。
本文件**只**回答两件事：**哪些控件归这里**、**本目录额外要守什么**。

上承 `projects/zml/AGENTS.md` 与仓库根 `AGENTS.md`；冲突时以更具体者为准
（本文件 > `../widgets/AGENTS.md` > `projects/zml/AGENTS.md` > 根 `AGENTS.md`）。

## 1. 什么样的控件归这里：**顶层控件**

**判据只有一条：这个控件不会在其他控件里被当作组件（子控件）使用。** 换言之，它只被
「装配层」（`ui/main.py`、`ui/setups/`、`zmlx/utils/` 等）打开成一个标签页，
**不会被任何 `QWidget` `addWidget()` 进去**。

配套的两条**必然推论**（都由这条判据直接推出）：

1. **依赖方向单向**：`tabs/` 可以 import `widgets/`；反过来，`widgets/` 里**一旦**有人
   import 了 `tabs/` 的东西，就说明那个 tabs 控件**正在被别人当组件用** —— 那它就不是
   顶层控件，**不该放在 `tabs/`**（该搬回 `widgets/`）。
2. **`tabs/` 内的控件彼此相对独立**：既然都是顶层控件，谁都不该是别人的零件。连
   「借用对方一个判定函数」也算越界 —— 那不是"当组件用"，但同样把两个页面绑在了一起。
   确有共用逻辑时，把它**下沉**到 [`../utils/lic_utils.py`](../utils/lic_utils.py) 之类的底层模块。

⚠️ **「实现了 `cleanup_before_tab_close()` / `refresh()`」不是判据，而是结果。** 一个顶层
控件自己管着生命周期（关标签时摘掉线程引用、切回来时刷新），所以它**通常**会实现这些
钩子；但钩子只是"顶层"的一个常见副产品，**不能反过来当作划分依据**。

⚠️ 反过来说：`tabs/` 里的控件**一旦**开始被别人当组件用，就该搬回 `widgets/`。

## 2. 什么样的控件**不**归这里（留 `../widgets/`）

| 类别 | 判据 | 例子 |
|---|---|---|
| **底层控件** | 会被别的控件 `addWidget()` 进去、或被继承 | `CodeEdit` / `TextBrowser` / `MarkdownView` / `MatplotWidget` / `Label` / `AttrView` 之外的那些；`ObjEditByText`；`editors.py`（被 `seepage.py` 用） |
| **宿主不是标签页的常驻控件** | 宿主是状态栏 / 右侧栏 / 标签容器，不是"打开一个页面" | `LicenseButton` / `VersionButton` / `RunStateLight` / `_parallel.py` 的 `CoreParallelEdit`（状态栏）、`OutputWidget`（右侧栏常驻，`closeable=False`）、`TabWidget`（标签容器） |
| **对话框 / 表单组件集** | 通过 `setup_ui()` 注册成「信息对话框」里的一行，不是页面 | `seepage.py` / `editors.py` / `float_edit.py` |

## 3. 当前成员（表中 3 个有效；2026-10-22 有 9 个、2026-10-30 有 1 个、2026-10-31 有 3 个随各插件移出，另有 12 个搬去 `setups/`，见表内划掉项）

| 控件 | 模块 | 生命周期钩子 |
|---|---|---|
| ~~`About`~~ | **已搬走**（2026-10-31）→ `setups/about.py` | 「关于」是软件自身的版本 / 路径 / 登录状态这一页 —— 状态栏版本按钮（`widgets/version_button.py`）与 ReadMe 右键菜单都指向它 ⇒ 属必加载的装配。同批接管了 `MainWindow.show_about`、那条 `add_action`（含它那个 `about()` 包装：先 `print(lic.desc)` 再开页）与 `app_data.get('show_about')` 那层**可替换实现**的间接。原模块与 `widget/about.py` 垫片删除、**不留垫片**。生命周期钩子（`cleanup_before_tab_close` + `refresh` + `showEvent`）一字未改 |
| ~~`AppPathEdit`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/viewers.py` | 只有「设置 → 路径」入口在用 |
| ~~`CheckCountView`~~ | **已搬走**（2026-10-31）→ `plugins/builtin/user_admin.py` | 随 `gui.show_check_count_view` 整体并入插件，原模块 `check_count_view.py` 删除、**不留垫片**（包级 `__getattr__` 也**没有**补转发 —— 与 2026-10-22 那批不同，这是用户明确要求的）。生命周期钩子（`cleanup_before_tab_close` + `refresh` + `showEvent`、`_Worker` / `_PrefillWorker` / `_UserListWorker` + 模块级 `_RUNNING_WORKERS`）一字未改 |
| ~~`CodeHistoryView`~~ | **已搬走**（2026-10-31）→ `setups/code_history_view.py` | 脚本执行历史被**控制台**与**代码编辑器**的右键菜单按命令名 `gui.show_code_history(...)` 调用（两处都在 `widgets/`，是通用控件）⇒ 属必加载的装配。同批接管了 `MainWindow.show_code_history`。原模块与 `widget/code_history_view.py` 垫片删除、**不留垫片** |
| ~~`CwdView`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/viewers.py` | 只有「文件 → 浏览 → 工作目录」入口在用 |
| ~~`DemoView`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/demo_menu.py` | 只有「示例浏览」插件在用，随 `show_demo` 并入插件 |
| ~~`EnvEdit`~~ | **已搬走**（2026-10-31）→ `setups/env_edit.py` | 「设置 → 系统」改的是**全局配置**、属产品功能（不该让用户在「设置 → 插件」里关掉），且带菜单项与快捷键 `Ctrl+E` ⇒ 属必加载的装配。同批接管了 `MainWindow.show_env_edit` 与那条 `add_action`。原模块与 `widget/env_edit.py` 垫片删除、**不留垫片** |
| ~~`FeedbackTool`~~ | **已搬走**（2026-10-31）→ `setups/feedback_tool.py` | 它是**出问题时的唯一出口**（ReadMe 的「新建Issue」链接指向它，别处也用它预填现场信息）⇒ 属必加载的装配。同批接管了 `MainWindow.show_feedback` 与那条 `add_action`（含 `text` 参数与「每段 text 各占一页 / 只在 `init` 里填」的语义；`is_enabled` 改用 `not gui.is_running()`）。原模块与 `widget/feedback_tool.py` 垫片删除、**不留垫片**。生命周期钩子（`cleanup_before_tab_close` + `save_file` + `need_save` + `showEvent`）一字未改 |
| ~~`FeedbacksView`~~ | **已搬走**（2026-10-31）→ `plugins/builtin/user_admin.py` | 随 `gui.show_feedbacks_view` 整体并入插件，原模块 `feedbacks_view.py` 与离线自测 `_test_feedbacks_view.py` 删除、**不留垫片**（包级 `__getattr__` 也**没有**补转发）。生命周期钩子（`cleanup_before_tab_close` + `refresh` + `showEvent`、`_ListWorker` / `_ReadWorker` / `_PrefillWorker` / `_UserListWorker` + 模块级 `_RUNNING_WORKERS`）一字未改 |
| ~~`Fn2Widget`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/fn2_view.py` | 只有「二维裂缝查看」插件在用，随 `show_fn2` 并入插件（连同 `GraphicsView` / `Hf2ColorMap` / `Hf2Data` / `Hf2FracView`） |
| ~~`GuiIteratorEdit`~~ | **已搬走**（2026-10-31）→ `setups/gui_iter_edit.py` | **这一页会被自动创建** —— `GuiIterator._plot_timing()` 在第一次绘图时直接 import 这个控件类并开标签页；做成插件的话那个自动化调用方根本不知道自己被关了 ⇒ 属必加载的装配。同批接管了 `MainWindow.show_gui_iter` 与那条 `add_action`（菜单 slot 由 `lambda: self.show_gui_iter(on_top=True)` 改成 `lambda: show_gui_iter(on_top=True)`，语义不变）。原模块删除、**不留垫片**。生命周期钩子（`refresh`）一字未改 |
| `ImageView` | `img.py` | ——（⚠️ 2026-10-22 曾随 `gui.open_image` 并入插件，**同日还原**：`open_image` 是底层能力，欢迎页在 `MainWindow` 构造期就要用） |
| ~~`ImageBrowser`~~ | **已搬走**（2026-10-30）→ `plugins/builtin/image_browser.py` | 控件与入口合进**同一个**自含插件文件（原先入口在插件、控件在本目录），原模块删除、**不留垫片**。只服务那一个可关闭的插件 ⇒ 按 `../plugins/AGENTS.md` §0.2「独立、完整」并入。生命周期钩子（`cleanup_before_tab_close` + `hideEvent`/`showEvent`、3 个后台线程、**故意不实现 `refresh()`**）一字未改 |
| ~~`LicenseRegister`~~ | **已搬走**（2026-10-31）→ `setups/license_register.py` | 「帮助 → 登录」的实体 —— 登录与授权检查是**软件本身**的一部分（状态栏按钮 `widgets/license_button.py`、`exts/_lic.py` 的失败引导都指向它）⇒ 属必加载的装配。同批接管了 `MainWindow.show_reg_tool` 与那条 `add_action`。⚠️ **`RegTool` 不动**：`show_reg_tool` 打开的是 `LicenseRegister`，`RegTool` 是另一回事。原模块与 `widget/license_register.py` 垫片删除、**不留垫片**。生命周期钩子（`cleanup_before_tab_close` + `showEvent`、`_Worker` 后台线程）一字未改 |
| ~~`UserAdminView`~~ | **已搬走**（2026-10-31）→ `plugins/builtin/user_admin.py` | 随 `gui.show_user_admin` 整体并入插件（原先装配在 `setups/user_admin.py`、控件在本目录）。只服务那一个可关闭的插件 ⇒ 按 `../plugins/AGENTS.md` §0.2「独立、完整」并入。原模块删除、**不留垫片**。生命周期钩子（`cleanup_before_tab_close` + `showEvent`、`_Jobs` / `_Worker` 后台线程）一字未改 |
| ~~`MemView`~~ | **已搬走**（2026-10-31）→ `setups/mem_view.py` | 变量浏览器连带 `app_data_edits` / `default_app_data_edit` 两个**全局**编辑器键，属必加载的装配；同批接管了 `MainWindow.show_memory` 与「显示 → 变量」菜单项。原模块与 `widget/mem_view.py` 垫片删除、**不留垫片** |
| ~~`MessageEdit`~~ | **已搬走**（2026-10-31）→ `setups/message.py` | 通知消息中心带去的是「落盘 API + 菜单入口」整块装配，属**必加载**（`gui.add_message` 是 main.py / plugins 的通用出口），所以搬去 `setups/` 而不是插件。原模块与 `widget/message.py` 垫片删除、**不留垫片** |
| ~~`OutputHistoryView`~~ | **已搬走**（2026-10-31）→ `setups/output_history_view.py` | 控制台输出历史被 `widgets/output_widget.py` 的右键菜单按命令名 `gui.show_output_history()` 调用（与「脚本运行历史」并列、同一条链）⇒ 属必加载的装配。同批接管了 `MainWindow.show_output_history`。原模块与 `widget/output_history_view.py` 垫片删除、**不留垫片** |
| ~~`PgConsole`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/pg_console.py` | 只有「Python 控制台」插件在用，随 `show_pg_console` 并入插件（⚠️ 缺 pyqtgraph 时那里是 `None`） |
| ~~`ReadMeBrowser`~~ | **已搬走**（2026-10-31）→ `setups/readme_browser.py` | 它是**欢迎页**（`main.py` 的 `__on_show` 启动时按 `show_readme` 设置自动打开），且带菜单项 / `F1` / **工具栏按钮** —— 做成插件会与「启动时显示欢迎页」互相打架 ⇒ 属必加载的装配。同批接管了 `MainWindow.show_readme` 与那条 `add_action`（含 `app_data.get('show_readme')` 那层**可替换实现**的间接）。原模块与 `widget/readme_browser.py` 垫片删除、**不留垫片** |
| `RegTool` | `reg_tool.py` | ——（已废弃；留作「离线授权码」那条老路。⚠️ **别与 `LicenseRegister` 搞混**：`gui.show_reg_tool` 打开的是后者，`RegTool` 早已不挂界面 —— 2026-10-31 搬走 `LicenseRegister` 时它**原地未动**） |
| ~~`PluginListEdit`~~ | **已搬走**（2026-10-31）→ `setups/plugin_list_edit.py` | 「设置 → 插件」是**插件机制的开关面板本身** —— 做成插件就成了「关掉『开关』」的循环（用户一取消勾选，就再也找不回「启用 / 禁用插件」这个入口）⇒ 属必加载的装配。同批接管了 `MainWindow.edit_setup_files` 与那条 `add_action`（命令名 `edit_setup_files` 与 action `name='setup_files'` 均为**命名遗留**，一个字未改）。原模块删除、**不留垫片**。`cleanup_before_tab_close`（旧名 `SetupFileEdit` / `setup_file_edit.py`，2026-10-18 改名，**不留转发层**；扫描走后台线程 `_ScanWorker`，`update_items()` 因此是**异步**的；⚠️ **构造时不加载数据**，由打开时的 `oper` 调 `update_items()`；扫描期间再来刷新请求只记一笔、铺完补一轮，避免反复重建表格）。⚠️ 方法名是 **`update_items` 而非 `refresh`**（2026-10-22）：`MainWindow.refresh()` 会在**每次切到这个标签页**时调 `get_current_widget().refresh()`，叫 `refresh` 会让这一页每次切回来都白算一遍（实测即「切标签卡顿」）。本控件的状态全由自己的交互触发（勾选 / 改优先级 / 临时加载 / 打开时的 `oper`），不依赖「切回时自动刷新」 |
| ~~`SolverSelector`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/solver_menu.py` | 只有「求解器」插件在用（随 `gui.show_solver_selector` 并入插件）。⚠️ 老路径 `from zmlx.ui.tabs import SolverSelector` 仍可用 —— 本包末尾的 PEP 562 `__getattr__` **惰性**转发到插件 |
| ~~`StringTable`~~ | **已搬走**（2026-10-31）→ `setups/string_table.py` | `gui.show_string_table` 是给**插件 / scen / 脚本**用的通用出口（`plugins/builtin/admin_menu.py` 4 处、`scen/ai_assistant/action.py`），做成插件就会让这些调用方在插件关掉时「找不到命令」⇒ 属必加载的装配。同批接管了 `MainWindow.show_string_table`（**返回值与 `set_parent=True` 原样保留**）。原模块与 `widget/string_table.py` 垫片删除、**不留垫片** |
| ~~`StyleSheetEdit`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/style_sheet_menu.py` | 只有「样式表」插件在用，随 `show_style_sheet` 并入插件 |
| ~~`TabDetailView`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/viewers.py` | 只有「显示 → 标签列表」入口在用 |
| `TextFileEdit` | `text_file_edit.py` | —— |
| ~~`TimerView`~~ | **已搬走**（2026-10-22）→ `plugins/builtin/viewers.py` | 只有「显示 → 耗时」入口在用 |

⚠️ 原随 `feedbacks_view` 同行的离线自测 `_test_feedbacks_view.py` 2026-10-31 **也已删除**：它并进了 `plugins/builtin/user_admin.py` 的 `test_4()`。

⚠️ **上表划掉的 13 个控件里，有 9 个仍可由本包按名字取用**：它们随插件搬走后，`tabs/__init__.py`
末尾用 PEP 562 `__getattr__` 做**惰性**转发（与 `SolverSelector` 同一套写法），所以
`from zmlx.ui.tabs import TimerView`（或 `DemoView` / `StyleSheetEdit` / `TabDetailView` /
`CwdView` / `AppPathEdit` / `Fn2Widget` / `PgConsole`）照常可用、2027-10-16 前不会断。
⚠️ **`UserAdminView` / `CheckCountView` / `FeedbacksView` 是例外：不留垫片**（2026-10-31，
用户明确要求）。`UserAdminView` 从来没有进过 `tabs/__init__.py` 的转发；`CheckCountView` 与
`FeedbacksView` 原来的静态转发**已删掉、也不再补惰性转发**，`widget/` 下对应的四个垫片
（`check_count_view.py` / `license_count.py` / `feedbacks_view.py` / `license_feedback.py`）
**一并删除**；`feedbacks_view` 的离线自测 `_test_feedbacks_view.py` 也随控件并进了插件。
三者全仓与外部工作区都没有别处 import，所以直接删。新代码请写
`from zmlx.ui.plugins.builtin.user_admin import UserAdminView, CheckCountView, FeedbacksView`。
⚠️ 只有真正取用时才会 import 插件模块；新代码请直接用
`from zmlx.ui.plugins.builtin.<插件> import <类>`。

⚠️ **上表与「有没有被 `tabs/__init__.py` 转发」无关**：2026-10-16 起，新增控件**默认不**在
`__init__.py` 里转发（要按子模块路径导入），`ImageBrowser` 就是没登记的那个（它后来更
整个搬去了插件，见上表划掉项）。完整规则见
[`../AGENTS.md`](../AGENTS.md) §1–§2；归属判据仍是本文件 §1 的「顶层性」。

⚠️ `closeEvent` **不在**上表里：关标签走 `deleteLater()`，**不发** `closeEvent`，
所以它是这条路径上的死代码 —— 详见 `../widgets/AGENTS.md` 的「销毁前的两次清理」。

## 4. 依赖方向：`tabs/` → `widgets/` → `utils/lic_utils.py`

| 方向 | 允许？ |
|---|---|
| `tabs/` import `zmlx.ui.widgets.*` | ✅ **可以** —— 标签页页面复用底层控件（如 `readme_browser` 继承 `md_view.MarkdownView`） |
| `tabs/` import `zmlx.ui.utils.lic_utils` | ✅ 可以 |
| `tabs/` import **同层**其它 tabs 控件 | ❌ **禁止** —— 顶层控件之间必须相对独立（见 §1 推论 2）。当前**实测为零** |
| `widgets/` import `zmlx.ui.tabs.*` | ❌ **禁止** —— 那说明该控件正在被别人当组件用，它该搬回 `widgets/`。（旧 `widget/` 下那些转发 shim 是兼容层、不是控件，**不算**违反；但它们已被整个 `widget/` 垫片取代） |

三层自下而上：`utils/lic_utils.py`（纯工具，无 Qt）→ `widgets/`（底层控件）→ `tabs/`（顶层页面）。
共用的东西**往下沉**，不要横向互相引用。

⚠️⚠️ **在 `tabs/` 里导入底层控件，必须走「子模块」路径**：

```python
from zmlx.ui.widgets.label import Label            # ✅ 子模块路径
from zmlx.ui.widgets import Label                  # ❌ 包级路径 —— 会抛循环导入
```

原因：`widgets/__init__.py` 会在导入期静态导入那些底层控件，链条是
`widgets/__init__` → `tabs/__init__` → `tabs/某个模块` → 回头找 `widgets.Label` ——
**那一刻 `widgets` 包还没执行到定义 `Label` 的那一行**，包级路径要在包的命名空间里取名字，
于是抛 `cannot import name 'Label' from partially initialized module`（2026-10-16 实测踩到，
`tabs/message.py` 因此改过 —— 它 2026-10-31 已搬去 `../setups/message.py`，那里只剩一条普通的子模块导入）。子模块路径只要求那个 `.py` 存在、不依赖包命名空间是否就绪，
所以不受影响。（函数体内延迟导入同样安全。）

⚠️ **同一类坑的第二处**（同日踩到）：`widget/__init__.py`（现在是垫片）若在导入期**静态**
import 本包的子模块，而本包里那些在**自己的顶层** import 底层控件的子模块，两头就会对撞（`partially initialized`）。
现已在该垫片里用 **PEP 562 的模块级 `__getattr__`** 惰性转发 —— 导入期一个 tabs
子模块都不碰，环随之消失。

## 5. 老路径仍然可用 —— 但**已弃用**（2027-10-16 删除）

⚠️ **2026-10-16 起 `widget/` 整个包都是兼容垫片**（同日由真控件包改名为 `widgets/`）——
它把**所有**老路径都转发过来，所以下面四条目前都还成立：

```python
from zmlx.ui.tabs import About                    # ✅ 推荐（无警告）
from zmlx.ui.tabs.about import About              # ✅ 推荐（无警告）
from zmlx.ui.widget import About                  # ⚠️ 老路径，发 DeprecationWarning
from zmlx.ui.widget.about import About            # ⚠️ 老路径，发 DeprecationWarning
```

⚠️⚠️ **弃用时间表**：2026-10-16 起弃用，**2027-10-16 删除**。三类转发都会在**导入时**
发出 :class:`DeprecationWarning`（`stacklevel=2`，指向调用者）：

| 转发层 | 位置 | 数量 |
|---|---|---|
| 模块级 shim | `widget/<模块>.py` | **28 个**（底层控件转 `widgets/`、顶层控件转 `tabs/`）。⚠️ 原为 44 个，2026-10-31 删掉 `check_count_view.py` / `license_count.py` / `feedbacks_view.py` / `license_feedback.py` / `message.py` / `mem_view.py` / `code_history_view.py` / `output_history_view.py` / `env_edit.py` / `string_table.py` / `readme_browser.py` / `license_register.py` / `feedback_tool.py` / `gui_iter_edit.py` / `about.py`（后十一个搬去 `setups/`，不是插件；`plugin_list_edit` 本无子模块 shim） |
| 包级惰性转发 | `widget/__init__.py` 的 `__getattr__`（仅 `tabs` 名字） | 12 个名字（`tabs` 表 1 个 + 插件表 11 个；2026-10-31 删掉 `CheckCountView` / `FeedbacksView` / `CodeHistoryView` / `OutputHistoryView` / `EnvEdit` / `StringTable` / `PluginListEdit` / `ReadMeBrowser` / `LicenseRegister` / `FeedbackTool` / `GuiIteratorEdit` / `About`） |
| 更早的旧名兼容层 | —— | **0 个**（`license_count.py` / `license_feedback.py` 均已于 2026-10-31 删除） |

- 之所以还要留这一年：老路径仍被**外部脚本**、**历史标签页的 `gui_restore`**（重启时按存下来的
  字符串重放）与**更早的兼容层**用着，直接删会打断它们。
- **新代码**：顶层控件用 `from zmlx.ui.tabs import X`；底层控件用
  `from zmlx.ui.widgets import X` —— 两条路径都**不会**产生任何警告。
- ⚠️ **不要往转发层里加逻辑** —— 它只做 import / 别名，新增能力一律加在本目录。
- ⚠️ 内部代码**不得**再走老路径：实测 `MainWindow` 构建全程 **0 条弃用警告**，
  这是「内部已清干净」的判据。若哪天冒出警告，说明有新代码用了老路径，应当场改掉。

⚠️ 改控件类名或模块名时，**旧的 `gui_restore` 字符串要还能解析**：历史标签页把
`gui.show_xxx()` 存进了标签状态，重启时按原文重放（见 `../plugins/builtin/user_admin.py`
末尾那几条旧名别名的写法与理由）。

## 6. 历史

- **2026-10-16**：三批迁入，共 **26 个**控件自 `../widget/` 迁来。
  - **第一批（5 个）**：`About` / `CheckCountView` / `FeedbackTool` / `FeedbacksView` /
    `LicenseRegister` —— 判据当时写作「实现了 `cleanup_before_tab_close()`」。
  - **第二批（8 个）**：`CwdView` / `DemoView` / `GuiIteratorEdit` / `MemView` /
    `MessageEdit` / `SolverSelector` / `TabDetailView` / `TimerView` —— 它们只有
    `refresh()`；判据随之放宽为「参与标签页生命周期」。
  - **第三批（13 个）**：`AppPathEdit` / `CodeHistoryView` / `EnvEdit` / `Fn2Widget` /
    `ImageView` / `OutputHistoryView` / `PgConsole` / `ReadMeBrowser` / `RegTool` /
    `SetupFileEdit` / `StringTable` / `StyleSheetEdit` / `TextFileEdit` —— 它们**没有**
    任何生命周期钩子；张老师由此把判据**换成真正的判据：顶层性**（见 §1），
    「有没有钩子」降级为"顶层的副产品"。
  - 同日，`is_admin_by_web_license`（原 `about.py`）与 `parse_user_list` 及其闭包
    （原 `check_count_view.py`）下沉到 `../lic_utils.py` —— 原先 `feedback_tool` /
    `feedbacks_view` 要跨控件借用它们，违反 §1 推论 2；下沉后本包**零跨控件依赖**。
  - 同日，`license_register.py` 的「答复解析与查询」工具段也已下沉为 `../lic_utils.py`。
- **2026-10-16（同日）新增** `ImageBrowser`（`image_browser.py`，图片浏览器）—— 本目录第一个
  **不是从 `widget/` 迁来、而是新写**的顶层控件，也是「顶层性」判据的现成范例：它只被装配层
  打开成标签页、不被任何控件复用。单文件自足（只依赖 `zmlx.ui.pyqt`），三个
  后台线程全部压低 OS 优先级。⚠️ **未**进 `__init__.py`，但**已挂到菜单**（见下方「同日：挂上菜单」）。
  ⚠️ **2026-10-30 已整体搬出本目录**（控件 + 入口合进 `../plugins/builtin/image_browser.py`，
  原模块删除、不留垫片）—— 它只服务那一个可关闭的插件，按「关掉功能时代码也一起关掉」
  并入才是对的住址。本节保留这段记录，是因为它当初正是「顶层性」判据的第一个实例。
- 迁移规模：`widget/` 原有 46 个 `.py` / 881 KB，其中绝大多数是顶层页面；迁移后
  `widget/` 只剩底层控件、宿主非标签页的常驻控件、对话框组件集，以及为这 26 个模块
  保留的转发层。
- **2026-10-16（同日）`ImageBrowser` 挂上菜单**「显示 → 图片浏览」，命令
  `gui.show_image_browser()`。⚠️ **挂载点不在 `main.py`，而在**
  [`../plugins/builtin/image_browser.py`](../plugins/builtin/image_browser.py) —— 这正是
  §1 那句「只被**装配层**打开成标签页」的实例：装配层包括 `setups/`，所以
  「新增一个入口」不该去动那个 2760 行的主窗口文件。`tabs/__init__.py` 依旧**没有**
  收它（挂载走子模块路径直接 import），这不影响它是顶层控件。
  同日连带修掉一个**空引用竞态**：扫描是异步的，「关标签时结果还在路上」是常态，
  而 `_on_scan_found` / `_on_thumb` / `_on_loaded` 三个回调没有像 `rescan()` 那样先判
  线程引用是否为 `None`（`cleanup_before_tab_close` 会把它们置 `None`），于是关标签
  瞬间会抛 `AttributeError: 'NoneType' object has no attribute 'submit_plan'`。
  ⚠️ 该缺陷**在挂菜单之前就存在**（用纯控件路径可独立复现，与菜单无关），
  只是因为挂上菜单后才真正面向用户，故一并修掉。
- **2026-10-16（同日）`ui/utils.py` 改成包 `ui/utils/`**：原 687 行的单文件按主题拆成
  `shared` / `gui_api` / `break_point` / `task_proc` / `file_handler`，并收编
  `background_task.py` 与 `lic_utils.py`。⚠️ **本包受影响的一行**：`lic_utils.py` 的路径
  由 `zmlx.ui.lic_utils` 变为 **`zmlx.ui.utils.lic_utils`** —— 本节（§4 的依赖方向表、
  §1 推论 2 的「下沉」范例）已同步；`tabs/` 下 6 个文件的 import 也已一并改掉
  （`about` / `check_count_view` / `feedback_tool` / `feedbacks_view` / `license_register`，
  以及 `widgets/license_button.py`）。**依赖方向本身没变**（依旧是
  `utils/lic_utils.py`（无 Qt）→ `widgets/` → `tabs/`），只是那个「纯工具」换了层门牌。
- **2026-10-18**：`SetupFileEdit` / `setup_file_edit.py` 改名为 **`PluginListEdit` /
  `plugin_list_edit.py`** —— `setup_file` 是「启动文件」这个旧叫法的残留，而这个控件管的是
  **插件**（`zml_plugin.py`），名字与职责对不上。⚠️ **不留转发层**：插件机制这块本仓与
  外部工作区都零引用，`from zmlx.ui.tabs.setup_file_edit import SetupFileEdit` 直接失效。
  `edit_setup_files` 与 action name `setup_files` 仍是旧名（见 `../ReadMe.md`
  的「命名遗留」表），只有控件本身改了名 —— **2026-10-31 该方法与控件一起搬去**
  `../setups/plugin_list_edit.py`，两个旧名照旧没动。
