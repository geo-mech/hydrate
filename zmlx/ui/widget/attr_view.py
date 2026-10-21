"""旧模块名（兼容层，**已弃用**）：``attr_view`` -> :mod:`zmlx.ui.widgets.attr_view`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/widgets/attr_view.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.ui.widgets.attr_view import ...``。

为什么留着而不删
----------------

2026-10-16 把包名由单数 ``widget`` 改为复数 ``widgets``（单数与 Qt 自己的
``QtWidgets`` 太像，读代码时极易看错）。但 ``from zmlx.ui.widget.attr_view import ...``
这条路径仍被三类来源用着，故留一年过渡：① 外部脚本与用户在控制台敲的命令；
② 历史标签页的 ``gui_restore``（重启时按存下来的字符串重放）；③ 更早的兼容层。

⚠️ 完整的兼容策略见 ``zmlx/ui/widget/__init__.py`` 与 ``widgets/AGENTS.md``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widget.attr_view`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.ui.widgets.attr_view``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.widgets.attr_view import *  # noqa: F401,F403
from zmlx.ui.widgets.attr_view import (  # noqa: F401
    AttrView,
    test
)
