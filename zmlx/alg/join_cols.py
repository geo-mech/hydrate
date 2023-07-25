from zml import *


def join_cols(*args):
    """
    将给定的多个vector作为列来合并成为一个np的矩阵
    """
    cols = []
    for v in args:
        if isinstance(v, Vector):
            a = np.zeros(shape=(v.size, 1), dtype=float)
            v.write_numpy(a)
            cols.append(a)
        else:
            v = np.reshape(np.asarray(v), (-1, 1))
            cols.append(v)
    return np.hstack(cols)
