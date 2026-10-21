"""已弃用的模块，请改用 zmlx.kr.base.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from zmlx.kr.base import create_fracture_kr

__all__ = ['create_fracture_kr']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    from zmlx.plt import plot_xy

    x, y = create_fracture_kr()
    plot_xy(x, y)
