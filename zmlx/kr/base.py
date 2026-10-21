"""旧模块名（兼容层，**已弃用**）：``base`` -> :mod:`zmlx.krs.base`.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/krs/base.py`` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.krs.base import ...``。

为什么留着而不删
----------------

2026-10-16 把包名由 ``zmlx.kr`` 改为 ``zmlx.krs`` —— 与 ``algs`` / ``utils`` /
``fluids`` / ``reactions`` / ``geometries`` / ``ui.widgets`` 统一用**复数**目录名。

但 ``from zmlx.kr.base import ...`` 这条路径仍被三类来源用着，故留一年过渡：
① 外部脚本与用户在控制台敲的命令；② 历史脚本 / 笔记里的 import；③ 更早的兼容层。

⚠️ 完整的兼容策略见 ``zmlx/kr/__init__.py``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.kr.base`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.krs.base``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.krs.base import *  # noqa: F401,F403

from zmlx.krs.base import (  # noqa: F401
    Interp1,
    create_fracture_kr,
    create_kr,
    create_krf,
    linspace,
)
