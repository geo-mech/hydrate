"""已弃用的模块，请改用 zmlx.tfc.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.tfc import list_fludefs

__all__ = [
    'list_fludefs'
]

warn('The zmlx.alg.list_fludefs module is deprecated, '
              'please use zmlx.base.seepage instead.',
              DeprecationWarning, stacklevel=2)
