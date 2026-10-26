"""旧模块名（兼容层，**已弃用**）：``editors`` -> :mod:`zmlx.ui.widgets.editors`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/ui/widgets/editors/`` 子包里
（2026-10-21 由单文件 ``widgets/editors.py`` 拆成子包，拆分后老路径不变）——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.ui.widgets.editors import ...``。

为什么留着而不删
----------------

2026-10-16 把包名由单数 ``widget`` 改为复数 ``widgets``（单数与 Qt 自己的
``QtWidgets`` 太像，读代码时极易看错）。但 ``from zmlx.ui.widget.editors import ...``
这条路径仍被三类来源用着，故留一年过渡：① 外部脚本与用户在控制台敲的命令；
② 历史标签页的 ``gui_restore``（重启时按存下来的字符串重放）；③ 更早的兼容层。

⚠️ 完整的兼容策略见 ``zmlx/ui/widget/__init__.py`` 与 ``widgets/AGENTS.md``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-21: 目标由单文件改为 ``widgets/editors/`` 子包（路径不变）
Modified by DeepSeek, 2026-10-22: 子包不再导出 ``setup_ui``（装配已移入插件），
    本文件的转发列表同步删除 —— 否则整条老路径会 ImportError
"""
from zmlx.system import warn


warn(
    '``zmlx.ui.widget.editors`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.ui.widgets.editors``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.ui.widgets.editors import *  # noqa: F401,F403
from zmlx.ui.widgets.editors import (  # noqa: F401
    ArrayEdit,
    ArrayTextEdit,
    DataEdit,
    Interp1Edit,
    Interp2Edit,
    NumpyAlgs,
    TextEdit,
    XyEdit,
    XyzEdit,
)
