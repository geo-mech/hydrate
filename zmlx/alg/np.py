"""
一些针对numpy的函数. 同时，也默认讲numpy内的内容引入. 因此，在大部分情况下，可以使用此模块来代替numpy
"""

from ctypes import c_double, POINTER

import numpy as np
from numpy import *  # 将numpy的内容引入


def get_pointer(data, dtype=None):
    """
    返回指针;
    """
    if not data.flags['C_CONTIGUOUS']:
        data = np.ascontiguous(data, dtype=data.dtype)  # 如果不是C连续的内存，必须强制转换

    if dtype is None:
        dtype = c_double

    return data.ctypes.data_as(POINTER(dtype))
