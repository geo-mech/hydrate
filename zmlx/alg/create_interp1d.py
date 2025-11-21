import zmlx.alg.sys as warnings

from zmlx.alg.interp import create_interp1d

warnings.warn(f'{__name__} will be removed after 2026-4-15, '
              f'please import from "zmlx.alg.interp" instead',
              DeprecationWarning,
              stacklevel=2)


def test():
    from zmlx.base.zml import np

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    f = create_interp1d(x=x, y=y, kind='nearest', bounds_error=False)

    print(f(0))
    print(f(-1))
    print(np.isnan(f(1000)))


if __name__ == '__main__':
    test()
