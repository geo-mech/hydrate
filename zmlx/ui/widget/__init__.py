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
_TABS = {
    'About': 'about',
    'AppPathEdit': 'app_path_edit',
    'CheckCountView': 'check_count_view',
    'CodeHistoryView': 'code_history_view',
    'CwdView': 'cwd_view',
    'DemoView': 'demo_view',
    'EnvEdit': 'env_edit',
    'FeedbackTool': 'feedback_tool',
    'FeedbacksView': 'feedbacks_view',
    'Fn2FracView': 'fn2',
    'Fn2Widget': 'fn2',
    'GraphicsView': 'fn2',
    'Hf2ColorMap': 'fn2',
    'Hf2Data': 'fn2',
    'ImageView': 'img',
    'LicenseRegister': 'license_register',
    'MemView': 'mem_view',
    'OutputHistoryView': 'output_history_view',
    'ReadMeBrowser': 'readme_browser',
    'RegTool': 'reg_tool',
    'PluginListEdit': 'plugin_list_edit',
    'StyleSheetEdit': 'style_sheet_edit',
    'TabDetailView': 'tab_detail_view',
    'TextFileEdit': 'text_file_edit',
    'TimerView': 'timer_view',
}


def __getattr__(name):
    """PEP 562：按需把 :mod:`zmlx.ui.tabs` 的名字转发过来（理由见上面那段 ⚠️）.

    ⚠️ **本转发已弃用**（2026-10-16 起，**2027-10-16** 删除）：它只为兼容老路径
    ``from zmlx.ui.widget import Xxx``。新代码请用 ``from zmlx.ui.tabs import Xxx``。
    """
    mod = _TABS.get(name)
    if mod is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
    import importlib

    warn(
        f'``zmlx.ui.widget.{name}`` 已弃用（2026-10-16）：控件已迁至 '
        f'``zmlx.ui.tabs.{mod}``；本兼容包将于 **2027-10-16** 删除。'
        f'请改用 ``from zmlx.ui.tabs import {name}``。',
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module(f'zmlx.ui.tabs.{mod}'), name)


def __dir__():
    return sorted(set(list(globals()) + list(_TABS)))
