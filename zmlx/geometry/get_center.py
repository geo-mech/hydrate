"""已弃用的模块，请改用 zmlx.geometry.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.geometry.base import get_center

__all__ = ['get_center']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(get_center(p1=(0, 0, 0), p2=(1, 0, 0)))
