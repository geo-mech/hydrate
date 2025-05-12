import warnings

from zmlx.alg.interp import interp1

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def _test():
    from zml import np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    xq = 3
    print(interp1(x, y, xq), np.sin(xq))
    xq = [4, 5]
    print(interp1(x, y, xq), np.sin(xq))


if __name__ == '__main__':
    _test()
