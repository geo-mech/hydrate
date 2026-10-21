"""旧控件包名（**兼容垫片，已弃用**）：``zmlx.ui.widget`` -> :mod:`zmlx.ui.widgets` / :mod:`zmlx.ui.tabs`.

⚠️⚠️ **本包整个是一层兼容垫片，将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。
导入本包**或本包下任何子模块**都会发出 :class:`DeprecationWarning`。

**新代码请写**：

======================  ==============================================
要什么                   写什么
======================  ==============================================
底层控件                 ``from zmlx.ui.widgets import CodeEdit``
                        （或 ``from zmlx.ui.widgets.code_edit import CodeEdit``）
顶层控件 / 标签页        ``from zmlx.ui.tabs import About``
======================  ==============================================

为什么改名为 ``widgets``（复数）
--------------------------------

单数 ``widget`` 与 Qt 自己的 ``QtWidgets`` 只差一个前缀，读代码时**极易看错**
（``zmlx.ui.widget.md_view`` 与 ``zmlx.ui.widgets.md_view`` 在 12 号字下几乎一样）。
改名为 ``widgets`` 后，也与 ``tabs`` / ``utils`` 这些**复数目录名**一致了。

⚠️ 顺带把一件事**归位**：原先 ``zmlx/ui/widget/`` 下混着两类东西 ——
① 真正的底层控件；② 26 个「转发到 ``tabs/``」的旧路径 shim（2026-10-16 控件分家时留下的）。
现在 ``widgets/`` 里**只有真控件**，②那种「只为兼容而存在」的转发全部集中到**本包**，
于是「哪里是兼容层」一眼可见：**整个 ``widget/`` 就是**。

⚠️ 本包的 ``__init__.py`` **不可省略**：没有它 ``zmlx.ui.widget`` 就不是一个包，
``from zmlx.ui.widget import About`` 与下面那些子模块 shim 全都失效 ——
垫片的价值正在于「老路径一条都不断」。

为什么留着而不删
----------------

``from zmlx.ui.widget.<模块> import <类>`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史标签页的 ``gui_restore``（重启时按存下来的
字符串重放）；③ 更早的兼容层（``license_count`` / ``license_feedback``）。

⚠️ 本包的**子模块**（``about.py`` / ``code_edit.py`` / …）也是一样的垫片，
各自转发到 ``widgets/`` 或 ``tabs/``。判据与依赖方向见 ``widgets/AGENTS.md`` 与
``tabs/AGENTS.md``。

Modified by DeepSeek, 2026-10-16: 由「真控件包」改为纯兼容垫片（真控件移到 widgets/）.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widget`` 已弃用（2026-10-16）：控件已迁至 ``zmlx.ui.widgets``（底层控件）与 '
    '``zmlx.ui.tabs``（顶层控件）；本兼容包将于 **2027-10-16** 删除。'
    '请改用 ``from zmlx.ui.widgets import ...`` 或 ``from zmlx.ui.tabs import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

# ---------------------------------------------------------------------------
# 底层控件：转发到 zmlx.ui.widgets（真控件在那儿）。
# ---------------------------------------------------------------------------

from zmlx.ui.widgets.code_edit import CodeEdit  # noqa: F401
from zmlx.ui.widgets.label import Label  # noqa: F401
from zmlx.ui.widgets.license_button import LicenseButton  # noqa: F401
from zmlx.ui.widgets.md_view import MarkdownView  # noqa: F401
from zmlx.ui.widgets.output_widget import OutputWidget  # noqa: F401
from zmlx.ui.widgets.plt import MatplotWidget  # noqa: F401
from zmlx.ui.widgets.tab_widget import TabWidget  # noqa: F401
from zmlx.ui.widgets.text_browser import TextBrowser  # noqa: F401
from zmlx.ui.widgets.version_button import VersionButton  # noqa: F401

# ---------------------------------------------------------------------------
# 顶层控件（在 zmlx.ui.tabs）：**惰性**转发。
#
# ⚠️ 这里**绝不能**写成顶层 ``from zmlx.ui.tabs.xxx import Xxx``。
#    ``tabs/`` 里的 ``code_history_view`` / ``output_history_view`` / ``readme_browser``
#    会在**自己的顶层** import ``widgets/`` 的底层控件；于是形成
#    「本包导入期 → tabs 子模块 → 回头要本包的名字」这个环，
#    Python 会抛 ``cannot import name ... from partially initialized module``
#    （2026-10-16 实测踩到）。
#    改成 PEP 562 的模块级 ``__getattr__`` 按需导入后，**导入期一个 tabs 子模块都不碰**，
#    环自然消失；对使用者完全无感：``from zmlx.ui.widget import About`` 照常可用。
# ---------------------------------------------------------------------------

#: 名字 -> 所属的 ``zmlx.ui.tabs`` 模块名。
#:
#: ⚠️ 只收**当年 ``widget/__init__.py`` 就导出过**的那些名字，**不扩大 API 面**。
#:
#: ⚠️ ``CheckCountView`` 2026-10-31 **已移出**：它随插件并入
#: ``plugins/builtin/user_admin.py``，本包对应的子模块 shim
#: (``widget/check_count_view.py`` 与更早的 ``widget/license_count.py``) 一并删除、
#: **不留垫片** —— 老路径 ``from zmlx.ui.widget import CheckCountView`` 现在会抛
#: ``AttributeError``，请改用 ``from zmlx.ui.plugins.builtin.user_admin import CheckCountView``。
#:
#: ⚠️ ``FeedbacksView`` 同日**也已移出**：子模块 shim ``widget/feedbacks_view.py`` 与
#: 更早的 ``widget/license_feedback.py`` 一并删除、**不留垫片**。
#:
#: ⚠️ ``MessageEdit`` 同日**也已移出**：通知消息中心搬去 ``setups/message.py``
#: （与 ``gui.show_messages`` 一起），子模块 shim ``widget/message.py`` 删除、
#: **不留垫片** —— 本表里本来就没有它，所以包级老路径本来也不可用。
#:
#: ⚠️ ``MemView`` 同日**也已移出**：变量浏览器搬去 ``setups/mem_view.py``
#: （连带「显示 → 变量」与 ``gui.show_memory``），子模块 shim
#: ``widget/mem_view.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``CodeHistoryView`` 同日**也已移出**：脚本执行历史搬去
#: ``setups/code_history_view.py``（连同 ``gui.show_code_history``），子模块 shim
#: ``widget/code_history_view.py`` 删除、**不留垫片** —— 请改用
#: ``from zmlx.ui.setups.code_history_view import CodeHistoryView``。
#:
#: ⚠️ ``OutputHistoryView`` 同日**也已移出**：控制台输出历史搬去
#: ``setups/output_history_view.py``（连同 ``gui.show_output_history``），子模块 shim
#: ``widget/output_history_view.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``EnvEdit`` 同日**也已移出**：「设置 → 系统」搬去 ``setups/env_edit.py``
#: （连同 ``gui.show_env_edit`` 与 ``Ctrl+E`` 菜单项），子模块 shim
#: ``widget/env_edit.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``StringTable`` 同日**也已移出**：通用字符串表格搬去
#: ``setups/string_table.py``（连同 ``gui.show_string_table``），子模块 shim
#: ``widget/string_table.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``PluginListEdit`` 同日**也已移出**：「设置 → 插件」搬去
#: ``setups/plugin_list_edit.py``（连同 ``gui.edit_setup_files``）——
#: 本表里本来就没有对应子模块 shim，包级老路径随之不可用。
#:
#: ⚠️ ``ReadMeBrowser`` 同日**也已移出**：「帮助 → ReadMe」搬去
#: ``setups/readme_browser.py``（连同 ``gui.show_readme``、``F1`` 与工具栏按钮），
#: 子模块 shim ``widget/readme_browser.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``LicenseRegister`` 同日**也已移出**：「帮助 → 登录」搬去
#: ``setups/license_register.py``（连同 ``gui.show_reg_tool``），子模块 shim
#: ``widget/license_register.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``FeedbackTool`` 同日**也已移出**：「帮助 → 反馈」搬去
#: ``setups/feedback_tool.py``（连同 ``gui.show_feedback``），子模块 shim
#: ``widget/feedback_tool.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``About`` 同日**也已移出**：「帮助 → 关于」搬去 ``setups/about.py``
#: （连同 ``gui.show_about`` 与 ``Ctrl+Shift+A``），子模块 shim
#: ``widget/about.py`` 删除、**不留垫片**。
#:
#: ⚠️ ``RegTool`` **仍然留在** ``tabs/``：``show_reg_tool`` 打开的是
#: ``LicenseRegister``，而 ``RegTool`` 是已下线、只留作「离线授权码」的那条旧路 ——
#: 两者不是一回事，别把它们一起搬。
_TABS = {
    'ImageView': 'img',
    'RegTool': 'reg_tool',
    'TextFileEdit': 'text_file_edit',
}

#: 名字 -> 插件模块（**不再是** ``zmlx.ui.tabs``）。
#:
#: ⚠️ 2026-10-22 起这些控件随各自的 ``show_xxx`` 并入插件（都只有那个插件在用），
#: ``tabs`` 里已经没有了。单列一张表是为了让「去哪找」一眼可见，也免得 ``_TABS``
#: 的说明与实际不符。
_PLUGINS = {
    'DemoView': 'zmlx.ui.plugins.builtin.demo_menu',
    'StyleSheetEdit': 'zmlx.ui.plugins.builtin.style_sheet_menu',
    'Fn2Widget': 'zmlx.ui.plugins.builtin.fn2_view',
    'GraphicsView': 'zmlx.ui.plugins.builtin.fn2_view',
    'Hf2ColorMap': 'zmlx.ui.plugins.builtin.fn2_view',
    'Hf2Data': 'zmlx.ui.plugins.builtin.fn2_view',
    'AppPathEdit': 'zmlx.ui.plugins.builtin.viewers',
    'CwdView': 'zmlx.ui.plugins.builtin.viewers',
    'TabDetailView': 'zmlx.ui.plugins.builtin.viewers',
    'TimerView': 'zmlx.ui.plugins.builtin.viewers',
    'SolverSelector': 'zmlx.ui.plugins.builtin.solver_menu',
}


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.ui.tabs`（或插件）的名字转发过来（理由见上面那段 ⚠️）.

    ⚠️ **本转发已弃用**（2026-10-16 起，**2027-10-16** 删除）：它只为兼容老路径
    ``from zmlx.ui.widget import Xxx``。新代码请用 ``from zmlx.ui.tabs import Xxx``。
    """
    mod = _TABS.get(name)
    plugin = _PLUGINS.get(name)
    if mod is None and plugin is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    if plugin is not None:
        warn(
            f'``zmlx.ui.widget.{name}`` 已弃用（2026-10-16）：控件已随插件迁至 '
            f'``{plugin}``；本兼容包将于 **2027-10-16** 删除。'
            f'请改用 ``from {plugin} import {name}``。',
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(importlib.import_module(plugin), name)

    warn(
        f'``zmlx.ui.widget.{name}`` 已弃用（2026-10-16）：控件已迁至 '
        f'``zmlx.ui.tabs.{mod}``；本兼容包将于 **2027-10-16** 删除。'
        f'请改用 ``from zmlx.ui.tabs import {name}``。',
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(f'zmlx.ui.tabs.{mod}'), name)


def __dir__():
    return sorted(set(list(globals()) + list(_TABS) + list(_PLUGINS)))
