"""旧模块名（兼容层，**已弃用**）：``style_sheet_edit`` -> :mod:`zmlx.ui.plugins.builtin.style_sheet_menu`.

⚠️ **本模块只是一层转发**，真正的实现在插件
``zmlx/ui/plugins/builtin/style_sheet_menu.py`` 里（2026-10-22 随 ``show_style_sheet``
一起搬入）—— 本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写**
``from zmlx.ui.plugins.builtin.style_sheet_menu import StyleSheetEdit``。

⚠️ 目标在 2026-10-22 变过一次：原来转发到 ``zmlx.ui.tabs.style_sheet_edit``，而
``StyleSheetEdit`` **只有「样式表」插件在用**，于是它随插件一起搬走（「完全自含」形态，
见 ``plugins/AGENTS.md`` §0.2）。本垫片随之改指新位置，老路径继续可用。

为什么留着而不删
----------------

2026-10-16 把「**顶层控件**」（只被装配层打开成一个标签页、**不会被任何控件当组件
（子控件）用**）集中迁到 ``zmlx/ui/tabs/``；本目录只留**底层控件**（会被
``addWidget()`` 进别处的、或被继承的）以及宿主不是标签页的常驻控件（状态栏按钮 /
右侧栏面板 / 标签容器 / 对话框组件集）。

但 ``from zmlx.ui.widgets.style_sheet_edit import StyleSheetEdit`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史标签页的 ``gui_restore``（重启时按存下来的
字符串重放）；③ 更早的兼容层（``license_count`` / ``license_feedback``）。

⚠️ 这是 ``ui`` → ``plugins`` 的**逆向 import**，只允许出现在兼容层（同
``ui/widgets/seepage.py`` 转发到 ``zmlx.ui.widgets.editors`` 的情形）。正常代码不要效仿。

Created by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-22: 目标改为 ``zmlx.ui.plugins.builtin.style_sheet_menu``
    （``StyleSheetEdit`` 随 show_style_sheet 并入插件）
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widgets.style_sheet_edit`` 已弃用（2026-10-16）：控件 ``StyleSheetEdit`` 已随插件搬到 '
    '``zmlx.ui.plugins.builtin.style_sheet_menu``；本转发层将于 **2027-10-16** 删除。'
    '请改用 ``from zmlx.ui.plugins.builtin.style_sheet_menu import StyleSheetEdit``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.plugins.builtin.style_sheet_menu import *  # noqa: F401,F403
from zmlx.ui.plugins.builtin.style_sheet_menu import (  # noqa: F401
    StyleSheetEdit,
    _ColorButton,
    _Qss,
    _StyleTextEdit
)
