"""已弃用的模块，请改用 zmlx.alg.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.base import *

__all__ = [
    'mass2str', 'time2str', 'fsize2str'
]


warn(f'{__name__} will be removed after 2026-5-8', DeprecationWarning,
              stacklevel=2)
