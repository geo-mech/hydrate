from scipy.interpolate import interp1d
import warnings


def create_interp1d(d=None, x=None, y=None, **kwargs):
    """
    利用一个包含了两列的numpy矩阵来创建一个一维的插值体
    """
    warnings.warn('please use scipy.interpolate.interp1d instead')
    if x is None or y is None:
        x = d[:, 0]
        y = d[:, 1]
    return interp1d(x, y, **kwargs)


def test():
    import numpy as np

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    f = create_interp1d(x=x, y=y, kind='nearest', bounds_error=False)

    print(f(0))
    print(f(-1))
    print(np.isnan(f(1000)))


if __name__ == '__main__':
    test()
