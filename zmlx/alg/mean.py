"""已弃用的模块，请改用 zmlx.alg.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.base import mean

__all__ = ['mean']


warn(
    f'The {__name__} will be removed after 2026-4-17, please import from zmlx instead.',
    DeprecationWarning, stacklevel=2)
