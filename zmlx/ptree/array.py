"""
导入numpy的array
"""
import os
from io import StringIO
import numpy as np
from zmlx.ptree.ptree import PTree


def _cast(data, pt=None):
    """
    从给定的数据构造array. 可能会返回None, 以及np的array (可能为空)
    """
    if isinstance(data, (list, tuple)):
        return np.array(data, dtype=float)

    if isinstance(data, (int, float)):
        return np.array([data], dtype=float)

    if isinstance(data, str):
        # 尝试文件
        fname = pt.find(data) if pt is not None else data
        if os.path.isfile(fname):
            return np.loadtxt(fname)
        # 尝试脚本
        try:
            return eval(data, {'np': np})
        except:
            pass
        # 尝试文本
        try:
            return np.loadtxt(StringIO(data))
        except:
            pass


def array(pt):
    """
    将PTree节点转化为numpy的array.
        可能会返回None, 以及np的array (可能为空)
    """
    assert isinstance(pt, PTree)
    return pt(cast=lambda data: _cast(data, pt))


def test():
    pt = PTree()
    pt.fill('x', [1, 2, 3])
    print(array(pt['x']))
    print(pt.data)


if __name__ == '__main__':
    test()
