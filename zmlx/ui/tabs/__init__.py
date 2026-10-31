"""顶层控件包（``zmlx.ui.tabs``）.

本包收纳**顶层控件** —— 它们只被装配层（``ui/main.py`` / ``ui/setups/`` /
``zmlx/utility/`` 等）打开成一个标签页，**不会被任何控件当组件（子控件）用**。
归属判据、与 ``zmlx/ui/widgets/`` 的分工见同目录的 ``AGENTS.md``。

⚠️ 两条硬约束：

1. **依赖单向**：``tabs/`` 可以复用 ``widgets/``，**反之不行** —— ``widgets/`` 一旦 import 了
   本包的东西，就说明那个控件正在被别人当组件用，那它该搬回 ``widgets/``。
2. **本包内控件相互独立**：顶层控件之间不得互相依赖（连"借用对方一个函数"也不行），
   共用的逻辑请**下沉**到 ``zmlx.ui.utils.lic_utils`` 之类的底层模块。

⚠️ **底层控件**（编辑器、浏览器、属性表……）与**宿主不是标签页的常驻控件**（状态栏按钮 /
右侧栏面板 / 标签容器 / 对话框组件集）**不在这里**，仍在 ``zmlx/ui/widgets/``。

⚠️ 老路径 ``from zmlx.ui.widget.<模块> import <类>`` 仍然可用 —— 整个 ``widget/`` 现在是
一层**兼容垫片**（导入即发 ``DeprecationWarning``，2027-10-16 删除），见该包的模块文档。

⚠️ **2026-10-22：部分控件随各自的插件搬走了**（`DemoView` / `Fn2Widget` / `PgConsole` /
`StyleSheetEdit` / `SolverSelector` / `TimerView` / `CwdView` / `TabDetailView` /
`AppPathEdit`）。为了不让老路径断掉，它们仍可由本包按名字取用 —— 由末尾的
``__getattr__`` **惰性转发**到插件模块（本包是兼容层）。**新代码**请直接写
``from zmlx.ui.plugins.builtin.<插件> import <类>``，或改用 ``gui.show_xxx()``。

Modified by DeepSeek, 2026-10-22: 搬进插件的 9 个控件补回包级**惰性**转发
    （`__getattr__` / `__dir__`），老路径 `from zmlx.ui.tabs import X` 不再失效
Modified by DeepSeek, 2026-10-31: `CheckCountView` 随插件并入
    `plugins/builtin/user_admin.py`（原 `check_count_view.py` 删除、**不留垫片**，
    **不补**惰性转发）；`UserAdminView` / `CheckCountView` / `FeedbacksView` 同一批搬走（均不留垫片）；
    `MessageEdit` / `MemView` 搬去 ``setups/``（也不是转发）
"""

# ⚠️ ``About`` 2026-10-31 **不再在这里**：「帮助 → 关于」整块（控件 + 菜单项 +
#    命令 ``gui.show_about``）搬进 ``setups/about.py``（状态栏版本按钮与 ReadMe
#    右键菜单都指向它，不该可关闭），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.about import About``，
#    或直接用 ``gui.show_about()``。
# ⚠️ ``CheckCountView`` 2026-10-31 **不再在这里**：控件随 `gui.show_check_count_view`
#    并入插件 ``plugins/builtin/user_admin.py``，原 ``check_count_view.py`` 删除、
#    **不留垫片**（包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.plugins.builtin.user_admin import CheckCountView``，
#    或直接用 ``gui.show_check_count_view()``。
# ⚠️ ``CodeHistoryView`` 2026-10-31 **不再在这里**：脚本执行历史控件连同命令
#    `gui.show_code_history` 一起搬进 ``setups/code_history_view.py``（它被控制台与代码
#    编辑器的右键菜单按**命令名**调用 ⇒ 属必加载的装配），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.code_history_view import CodeHistoryView``，
#    或直接用 ``gui.show_code_history(folder=...)``。
# ⚠️ ``DemoView`` 2026-10-22 **不再静态转发**：它随 `show_demo` 整体并入插件
#    ``plugins/builtin/demo_menu.py``（只有那个插件在用）。新代码请写
#    ``from zmlx.ui.plugins.builtin.demo_menu import DemoView``；
#    老路径 ``from zmlx.ui.tabs import DemoView`` 仍可用（见末尾 ``__getattr__``）。
# ⚠️ ``EnvEdit`` 2026-10-31 **不再在这里**：「设置 → 系统」整块（控件 + 菜单项
#    + 命令 ``gui.show_env_edit``）搬进 ``setups/env_edit.py``（它改的是**全局配置**、
#    属产品功能，且带菜单项与快捷键 ``Ctrl+E``），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.env_edit import EnvEdit``，
#    或直接用 ``gui.show_env_edit()``。
# ⚠️ ``FeedbackTool`` 2026-10-31 **不再在这里**：「帮助 → 反馈」整块（控件 + 菜单项
#    + 命令 ``gui.show_feedback``）搬进 ``setups/feedback_tool.py``（它是出问题时的
#    唯一出口，不该可关闭），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.feedback_tool import FeedbackTool``，
#    或直接用 ``gui.show_feedback(text=...)``。
# ⚠️ ``FeedbacksView`` 2026-10-31 **不再在这里**：控件随 `gui.show_feedbacks_view`
#    并入插件 ``plugins/builtin/user_admin.py``，原 ``feedbacks_view.py`` 与它的离线
#    自测 ``_test_feedbacks_view.py`` 一并删除、**不留垫片**（包级 `__getattr__`
#    也**没有**它的转发）。新代码请写
#    ``from zmlx.ui.plugins.builtin.user_admin import FeedbacksView``，
#    或直接用 ``gui.show_feedbacks_view()``。
# ⚠️ ``Fn2Widget`` 2026-10-22 **不再静态转发**：它随 `show_fn2` 整体并入插件
#    ``plugins/builtin/fn2_view.py``；新代码请从插件模块导入，
#    老路径 ``from zmlx.ui.tabs import Fn2Widget`` 仍可用（末尾惰性转发）。
# ⚠️ ``GuiIteratorEdit`` 2026-10-31 **不再在这里**：「设置 → 迭代器」整块（控件 +
#    菜单项 + 命令 ``gui.show_gui_iter``）搬进 ``setups/gui_iter_edit.py``（这一页
#    会被 ``GuiIterator._plot_timing()`` **自动创建**，不该可关闭），原模块删除、
#    **不留垫片**（包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.gui_iter_edit import GuiIteratorEdit``，
#    或直接用 ``gui.show_gui_iter()``。
from zmlx.ui.tabs.img import ImageView
# ⚠️ ``LicenseRegister`` 2026-10-31 **不再在这里**：「帮助 → 登录」整块（控件 + 菜单项
#    + 命令 ``gui.show_reg_tool``）搬进 ``setups/license_register.py``（登录与授权检查
#    是软件本身的一部分，不该可关闭），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.license_register import LicenseRegister``，
#    或直接用 ``gui.show_reg_tool()``。
# ⚠️ ``MemView`` 2026-10-31 **不再在这里**：变量浏览器搬进 ``setups/mem_view.py``
#    （连带「显示 → 变量」菜单项与命令 ``gui.show_memory``），原模块删除、
#    **不留垫片**（包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.mem_view import MemView``，
#    或直接用 ``gui.show_memory()``。
# ⚠️ ``MessageEdit`` 2026-10-31 **不再在这里**：通知消息中心是 ``setups`` 的
#    装配（不是插件），随 ``gui.show_messages`` 一起搬到 ``setups/message.py``，
#    原模块删除、**不留垫片**（包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.message import MessageEdit``，
#    或直接用 ``gui.show_messages()``。
# ⚠️ ``OutputHistoryView`` 2026-10-31 **不再在这里**：控制台输出历史控件连同命令\n#    `gui.show_output_history` 一起搬进 ``setups/output_history_view.py``（它与\n#    ``code_history_view`` 是同一条链，被控制台右键菜单按命令名调用），原模块删除、\n#    **不留垫片**（包级 `__getattr__` 也**没有**它的转发）。\n#    新代码请写 ``from zmlx.ui.setups.output_history_view import OutputHistoryView``，\n#    或直接用 ``gui.show_output_history()``。\n# ⚠️ ``TimerView`` / ``CwdView`` / ``TabDetailView`` / ``AppPathEdit`` 2026-10-22 随
#    ``show_*`` 并入插件 ``plugins/builtin/viewers.py``；包级老路径仍可用（末尾惰性转发）。
# ⚠️ ``PgConsole`` 2026-10-22 **不再静态转发**：它随 `show_pg_console` 并入插件
#    ``plugins/builtin/pg_console.py``（⚠️ 缺 pyqtgraph 时那里是 `None`）；
#    包级老路径仍可用（末尾惰性转发）。
# ⚠️ ``PluginListEdit`` 2026-10-31 **不再在这里**：「设置 → 插件」整块（控件 + 菜单项
#    + 命令 ``gui.edit_setup_files``）搬进 ``setups/plugin_list_edit.py``（它是插件机制的
#    开关面板本身，做成插件就再也找不回这个入口），原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.plugin_list_edit import PluginListEdit``，
#    或直接用 ``gui.edit_setup_files()``。
# ⚠️ ``ReadMeBrowser`` 2026-10-31 **不再在这里**：「帮助 → ReadMe」（欢迎页）整块
#    （控件 + 菜单项 + `F1` + 工具栏按钮 + 命令 ``gui.show_readme``）搬进
#    ``setups/readme_browser.py``，原模块删除、**不留垫片**
#    （包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.readme_browser import ReadMeBrowser``，
#    或直接用 ``gui.show_readme()``。
from zmlx.ui.tabs.reg_tool import RegTool
# ⚠️ ``SolverSelector`` 2026-10-22 **不再静态转发**：它随 ``show_solver_selector``
#    整体并入插件 ``plugins/builtin/solver_menu.py``；包级老路径仍可用（末尾惰性转发）。
# ⚠️ ``StringTable`` 2026-10-31 **不再在这里**：通用字符串表格连同命令
#    ``gui.show_string_table`` 一起搬进 ``setups/string_table.py``（它是给插件 / scen /
#    脚本用的通用出口，`admin_menu` 与 `ai_assistant` 按命令名调用它），
#    原模块删除、**不留垫片**（包级 `__getattr__` 也**没有**它的转发）。
#    新代码请写 ``from zmlx.ui.setups.string_table import StringTable``，
#    或直接用 ``gui.show_string_table(data, caption)``。
# ⚠️ ``StyleSheetEdit`` 2026-10-22 **不再静态转发**：它随 `show_style_sheet` 并入插件
#    ``plugins/builtin/style_sheet_menu.py``；包级老路径仍可用（末尾惰性转发）。
from zmlx.ui.tabs.text_file_edit import TextFileEdit


#: 名字 -> ``(插件模块, 属性名)``：2026-10-22 随各自插件搬走的控件，本包按名字**惰性**
#: 转发（PEP 562）。⚠️ 只有真正取用时才 import 插件模块 —— 本包在导入期就会执行，
#: 静态 import 等于「import 一下标签页包就把插件拉起来」，还可能撞上循环导入。
_PLUGINS = {
    'SolverSelector': ('zmlx.ui.plugins.builtin.solver_menu', 'SolverSelector'),
    'TimerView': ('zmlx.ui.plugins.builtin.viewers', 'TimerView'),
    'CwdView': ('zmlx.ui.plugins.builtin.viewers', 'CwdView'),
    'TabDetailView': ('zmlx.ui.plugins.builtin.viewers', 'TabDetailView'),
    'AppPathEdit': ('zmlx.ui.plugins.builtin.viewers', 'AppPathEdit'),
    'DemoView': ('zmlx.ui.plugins.builtin.demo_menu', 'DemoView'),
    'StyleSheetEdit': ('zmlx.ui.plugins.builtin.style_sheet_menu', 'StyleSheetEdit'),
    'Fn2Widget': ('zmlx.ui.plugins.builtin.fn2_view', 'Fn2Widget'),
    'PgConsole': ('zmlx.ui.plugins.builtin.pg_console', 'PgConsole'),
}


def __getattr__(name):
    """惰性转发到插件模块（PEP 562）：老路径 ``from zmlx.ui.tabs import X`` 仍然可用.

    ⚠️ ``PgConsole`` 可能是 ``None``（缺 ``pyqtgraph`` 时插件里就是 ``None``），
    调用方要自己判空 —— 与老 ``tabs/pg.py`` 的行为一致。
    """
    target = _PLUGINS.get(name)
    if target is not None:
        module, attr = target
        import importlib
        return getattr(importlib.import_module(module), attr)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    """让 ``dir(zmlx.ui.tabs)`` 也列出惰性转发的名字."""
    return sorted(set(list(globals()) + list(_PLUGINS)))
