"""已弃用的模块，请改用 zmlx.algs.interp.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.algs.interp import create_interp1d

warn(f'{__name__} will be removed after 2026-4-15, '
              f'please import from "zmlx.algs.interp" instead',
              DeprecationWarning,
              stacklevel=2)


def test():
    from zmlx.exts import np

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    f = create_interp1d(x=x, y=y, kind='nearest', bounds_error=False)

    print(f(0))
    print(f(-1))
    print(np.isnan(f(1000)))


if __name__ == '__main__':
    test()
