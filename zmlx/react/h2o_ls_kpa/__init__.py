"""旧子包名（兼容层，**已弃用**）：``h2o_ls_kpa`` -> :mod:`zmlx.reactions.h2o_ls_kpa`.

⚠️ **本子包只是一层转发**：它下面的每个模块在 ``zmlx/react/h2o_ls_kpa/`` 里各留了一层
同名转发；本文件再把子包 ``__init__`` **自己**导出的名字转出来。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.reactions.h2o_ls_kpa import ...``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.react.h2o_ls_kpa`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.reactions.h2o_ls_kpa``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.reactions.h2o_ls_kpa import *  # noqa: F401,F403
from zmlx.reactions.h2o_ls_kpa import (  # noqa: F401
    create
)
