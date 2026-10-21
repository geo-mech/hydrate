"""已弃用的模块，请改用 zmlx.exts.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.exts import make_parent

__all__ = ['make_parent']


warn(f'The module {__name__} will be removed after 2026-4-15, import make_parent from "zml" instead',
              DeprecationWarning, stacklevel=2)
