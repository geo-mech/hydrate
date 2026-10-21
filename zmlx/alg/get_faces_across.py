"""已弃用的模块，请改用 zmlx.alg.faces_across.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.alg.faces_across import get_faces_across

__all__ = ['get_faces_across']
warn('The modulus get_faces_across is deprecated '
              '(will be removed after 2026-4-9). '
              'please use zmlx.base.faces_across instead.',
              DeprecationWarning, stacklevel=2)
