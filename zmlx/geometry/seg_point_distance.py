"""已弃用的模块，请改用 zmlx.geometry.segment.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.geometry.segment import seg_point_distance

__all__ = ['seg_point_distance']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    p1 = (0, 0, 0)
    p2 = (1, 0, 0)
    p3 = (2, 0, 0)
    print(seg_point_distance((p1, p2), p3))
