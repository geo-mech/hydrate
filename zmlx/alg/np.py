"""
一些针对numpy的函数. 同时，也默认讲numpy内的内容引入. 因此，在大部分情况下，可以使用此模块来代替numpy
"""

from ctypes import c_double, POINTER

import numpy as np


def get_pointer(data, dtype=None):
    """
    返回指针;
    """
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
