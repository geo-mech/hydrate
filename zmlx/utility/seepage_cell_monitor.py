"""旧模块名（兼容层，**已弃用**）：``seepage_cell_monitor`` -> :mod:`zmlx.utils.seepage_cell_monitor`.

⚠️ **本模块只是一层转发**，真正的实现全在 :mod:`zmlx.utils.seepage_cell_monitor` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.utils.seepage_cell_monitor import ...``。

为什么留着而不删
----------------

2026-10-16 把包名由 ``zmlx.utility`` 改为 ``zmlx.utils`` —— 与 ``zmlx.ui.utils``
统一拼写（``utility`` 只是 ``utils`` 的同义词，两种写法并存只会让人犹豫用哪个）。

但 ``from zmlx.utility.{mod} import ...`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史脚本 / 笔记里的 import；③ 更早的兼容层。

⚠️ 完整的兼容策略见 ``zmlx/utility/__init__.py``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.utility.seepage_cell_monitor`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.utils.seepage_cell_monitor``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.utils.seepage_cell_monitor import *  # noqa: F401,F403
