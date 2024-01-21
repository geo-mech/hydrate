from scipy.interpolate import interp1d


def interp1(x, y, xq, kind='linear'):
    """
    实施一维的插值，类似Matlab的interp1函数
    """
    f = interp1d(x, y, kind=kind)
    return f(xq)


def _test():
    import numpy as np
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    xq = 3
    print(interp1(x, y, xq), np.sin(xq))
    xq = [4, 5]
    print(interp1(x, y, xq), np.sin(xq))


if __name__ == '__main__':
    _test()
