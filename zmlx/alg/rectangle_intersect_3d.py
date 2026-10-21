"""已弃用的模块，请改用 zmlx.geometries.rect_3d_intersection.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.geometries.rect_3d_intersection import *

_keep = [print_enable]

warn(f'{__name__} will be removed after 2026-12-23', DeprecationWarning,
              stacklevel=2)
