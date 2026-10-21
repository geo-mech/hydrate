"""已弃用的模块，请改用 zmlx.geometries.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.geometries.base import point_distance as get_point_distance

__all__ = ['get_point_distance']

warn('The modulus get_point_distance is deprecated '
              '(will be removed after 2026-4-9), '
              'please use zmlx.geometries.point_distance instead.',
              DeprecationWarning, stacklevel=2)
