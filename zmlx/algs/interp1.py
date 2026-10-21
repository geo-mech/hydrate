"""已弃用的模块，请改用 zmlx.algs.interp.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.algs.interp import interp1

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def _test():
    from zmlx.exts import np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    xq = 3
    print(interp1(x, y, xq), np.sin(xq))
    xq = [4, 5]
    print(interp1(x, y, xq), np.sin(xq))


if __name__ == '__main__':
    _test()
