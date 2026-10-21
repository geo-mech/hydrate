"""已弃用的模块，请改用 zmlx.alg.frac.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.alg.frac import get_frac_cond, g_1cm

__all__ = ['get_frac_cond', 'g_1cm']


warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)
