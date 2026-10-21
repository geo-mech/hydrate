"""
裂缝相关的算法

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.scen.frac import get_fn2

__all__ = [
    "get_fn2"
]


warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)
