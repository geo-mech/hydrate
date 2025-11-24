"""
一些针对numpy的函数. 同时，也默认讲numpy内的内容引入. 因此，在大部分情况下，可以使用此模块来代替numpy
"""
from ctypes import c_double, POINTER

import zmlx.alg.sys as warnings
from zmlx.base.zml import get_pointer64, np


def get_pointer(data, dtype=None):
    """
    返回指针;
    """
    warnings.warn(
        f'The {__name__}.get_pointer will be removed after 2026-4-17, '
        f'please use zmlx.get_pointer64 instead.',
        DeprecationWarning, stacklevel=2)

    if dtype is None or dtype == c_double or dtype == float or dtype == np.float64:
        return get_pointer64(data)

    if not data.flags.c_contiguous:
        data = np.ascontiguousarray(data)

    if dtype is None:
        dtype = c_double

    return data.ctypes.data_as(POINTER(dtype))


if __name__ == '__main__':
    a = np.linspace(0, 3, 10)
    print(a)
    p = get_pointer(a)
    p[2] = 123
    print(a)
