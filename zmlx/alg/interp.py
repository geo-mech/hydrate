"""
插值相关的函数
"""
try:
    from scipy.interpolate import interp1d
except ImportError:
    interp1d = None


def create_interp1d(d=None, x=None, y=None, **kwargs):
    """
    利用一个包含了两列的numpy矩阵来创建一个一维的插值体
    """
    assert interp1d is not None, 'scipy.interpolate.interp1d is not installed.'
    if x is None or y is None:
        x = d[:, 0]
        y = d[:, 1]
    return interp1d(x, y, **kwargs)


def interp1(x, y, xq, kind='linear'):
    """
    实施一维的插值，类似Matlab的interp1函数
    """
    assert interp1d is not None, 'scipy.interpolate.interp1d is not installed.'
    f = interp1d(x, y, kind=kind)
    return f(xq)
