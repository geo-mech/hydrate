"""旧模块名（兼容层，**已弃用**）：``seepage_numpy`` -> :mod:`zmlx.tfc`.

⚠️ **本模块只是一层转发**，真正的实现全在 :mod:`zmlx.tfc` 里 ——
本文件除了下面那几行 import / 别名不该再有任何内容。

⚠️⚠️ **本转发层将于 2027-10-16 删除**（2026-10-16 起弃用，保留一年）。导入本模块时
会发出 :class:`DeprecationWarning`。**新代码请写** ``from zmlx.tfc import ...``。

⚠️ **本模块在改名之前就已经是弃用垫片了**（那时它转发到本包的小写兄弟模块）。
本次包改名后，它继续作为垫片存在，只是目标换成了新包 —— 于是一条老路径都没断。
它**没有**被搬进 ``zmlx.utils``（已弃用的东西不往新包里带），
所以它是「旧名 -> 最终实现」的**直连**转发。

⚠️ 完整的兼容策略见 ``zmlx/utility/__init__.py``。

Modified by DeepSeek, 2026-10-16

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn


warn(
    '``zmlx.utility.seepage_numpy`` 已弃用（2026-10-16）：请改用 '
    '``zmlx.tfc``；本转发层将于 **2027-10-16** 删除。',
    DeprecationWarning,
    stacklevel=2,
)

from zmlx.tfc import (  # noqa: F401
    SeepageNumpy,
    as_numpy
)

__all__ = ['SeepageNumpy', 'as_numpy']
