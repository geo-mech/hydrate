try:
    from scipy.interpolate import interp1d
except Exception as e:
    print(e)
    interp1d = None


def create_interp1d(d=None, x=None, y=None, **kwargs):
    """
    利用一个包含了两列的numpy矩阵来创建一个一维的插值体
    """
    if x is None or y is None:
        x = d[:, 0]
        y = d[:, 1]
    return interp1d(x, y, **kwargs)


def interp1(x, y, xq, kind='linear'):
    """
    实施一维的插值，类似Matlab的interp1函数
    """
    f = interp1d(x, y, kind=kind)
    return f(xq)
