from zmlx.kr.pre_defines import create_krf
__all__ = ['create_krf']

import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)








def _test1():
    from zml import plot
    x, y = create_krf(0.05, 3)
    print(x)
    print(y)

    def f(fig):
        ax = fig.subplots()
        ax.plot(x, y)

    plot(f)


def _test2():
    from zml import plot
    x, y = create_krf(0.1, 1.5, k_max=100, s_max=1, count=1000)
    print(x)
    print(y)

    def f(fig):
        ax = fig.subplots()
        ax.plot(x, y)

    plot(f)


def _test3():
    from zmlx.ui import plot
    x, y = create_krf(0.3, 2, k_max=1, s_max=1, count=100)
    print(x)
    print(y)

    def f(fig):
        ax = fig.subplots()
        ax.plot(x, y)

    plot(f)


if __name__ == '__main__':
    _test3()
