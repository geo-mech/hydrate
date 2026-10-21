"""已弃用的模块，请改用 zmlx.geometry.point.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.geometry.point import get_angle

_keep = [get_angle]


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)
