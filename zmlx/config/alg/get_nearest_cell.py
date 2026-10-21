"""已弃用的模块，请改用 zmlx.exts.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.exts import get_nearest_cell

warn(
    'This module is deprecated (will be removed after 2026-4-9), use zmlx.algs.nearest_cell instead',
    DeprecationWarning, stacklevel=2)

__all__ = [
    "get_nearest_cell",
]
