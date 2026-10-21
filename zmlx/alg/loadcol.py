"""已弃用的模块，请改用 zmlx.io.load_col.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.io.load_col import load_col as loadcol

__all__ = ['loadcol']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)
