# -*- coding: utf-8 -*-

from scipy.interpolate import interp1d


def create_interp1d(d, kind='linear'):
    """
    利用一个包含了两列的numpy矩阵来创建一个一维的插值体
    """
    x = d[:, 0]
    y = d[:, 1]
    return interp1d(x, y, kind=kind)
