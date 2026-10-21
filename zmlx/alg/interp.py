"""旧模块名（兼容层，**已改名为** :mod:`zmlx.algs.interp`）.

⚠️ **本模块只是一层转发**，真正的实现全在 ``zmlx/algs/interp.py`` 里。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时会发出
:class:`DeprecationWarning`。**新代码请写** ``from zmlx.algs.interp import ...``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.alg.interp`` 已弃用（2026-10-16）：算法包已改名为 ``zmlx.algs``；'
    '本转发层将于 **2027-10-16** 删除。请改用 ``from zmlx.algs.interp import ...``。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.algs.interp import *  # noqa: F401,F403
from zmlx.algs.interp import (  # noqa: F401
    create_interp1d,
    interp1
)
