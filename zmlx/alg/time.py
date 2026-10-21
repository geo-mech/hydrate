"""已弃用的模块，请改用 zmlx.alg.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.base import year_to_seconds

__all__ = ['year_to_seconds']


warn(f'The {__name__} will be removed after 2026-4-17',
              DeprecationWarning, stacklevel=2)
