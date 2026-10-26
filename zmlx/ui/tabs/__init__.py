"""顶层控件包（``zmlx.ui.tabs``）.

本包收纳**顶层控件** —— 它们只被装配层（``ui/main.py`` / ``ui/extra_setups/`` /
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
"""

from zmlx.ui.tabs.about import About
from zmlx.ui.tabs.check_count_view import CheckCountView
from zmlx.ui.tabs.code_history_view import CodeHistoryView
# ⚠️ ``DemoView`` 2026-10-22 **不再静态转发**：它随 `show_demo` 整体并入插件
#    ``plugins/builtin/demo_menu.py``（只有那个插件在用）。新代码请写
#    ``from zmlx.ui.plugins.builtin.demo_menu import DemoView``；
#    老路径 ``from zmlx.ui.tabs import DemoView`` 仍可用（见末尾 ``__getattr__``）。
from zmlx.ui.tabs.env_edit import EnvEdit
from zmlx.ui.tabs.feedback_tool import FeedbackTool
from zmlx.ui.tabs.feedbacks_view import FeedbacksView
# ⚠️ ``Fn2Widget`` 2026-10-22 **不再静态转发**：它随 `show_fn2` 整体并入插件
#    ``plugins/builtin/fn2_view.py``；新代码请从插件模块导入，
#    老路径 ``from zmlx.ui.tabs import Fn2Widget`` 仍可用（末尾惰性转发）。
from zmlx.ui.tabs.gui_iter_edit import GuiIteratorEdit
from zmlx.ui.tabs.img import ImageView
from zmlx.ui.tabs.license_register import LicenseRegister
from zmlx.ui.tabs.mem_view import MemView
from zmlx.ui.tabs.message import MessageEdit
from zmlx.ui.tabs.output_history_view import OutputHistoryView
# ⚠️ ``TimerView`` / ``CwdView`` / ``TabDetailView`` / ``AppPathEdit`` 2026-10-22 随
#    ``show_*`` 并入插件 ``plugins/builtin/viewers.py``；包级老路径仍可用（末尾惰性转发）。
# ⚠️ ``PgConsole`` 2026-10-22 **不再静态转发**：它随 `show_pg_console` 并入插件
#    ``plugins/builtin/pg_console.py``（⚠️ 缺 pyqtgraph 时那里是 `None`）；
#    包级老路径仍可用（末尾惰性转发）。
from zmlx.ui.tabs.plugin_list_edit import PluginListEdit
from zmlx.ui.tabs.readme_browser import ReadMeBrowser
from zmlx.ui.tabs.reg_tool import RegTool
# ⚠️ ``SolverSelector`` 2026-10-22 **不再静态转发**：它随 ``show_solver_selector``
#    整体并入插件 ``plugins/builtin/solver_menu.py``；包级老路径仍可用（末尾惰性转发）。
from zmlx.ui.tabs.string_table import StringTable
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
