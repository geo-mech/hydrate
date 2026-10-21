"""已弃用的模块，请改用 zmlx.geometry.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""
from zmlx.system import warn
from numpy.linalg import norm as get_norm

__all__ = ['get_norm']


warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

if __name__ == '__main__':
    print(get_norm([3, 4]))
