# -*- coding: utf-8 -*-


from zml import *


def join_cols(*args):
    """
    将给定的多个Vector作为列来合并成为一个np的矩阵
    """
    cols = []
    for v in args:
        if not isinstance(v, Vector):
            v = Vector(value=v)
        a = np.zeros(shape=(v.size, 1), dtype=float)
        v.write_numpy(a)
        cols.append(a)
    return np.concatenate(cols, axis=1)

