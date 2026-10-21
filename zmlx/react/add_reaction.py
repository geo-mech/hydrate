"""已弃用的模块，请改用 zmlx.react.alg.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.react.alg import add_reaction

__all__ = [
    'add_reaction'
]


warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, please '
              f'import from zmlx instead',
              DeprecationWarning, stacklevel=2)
