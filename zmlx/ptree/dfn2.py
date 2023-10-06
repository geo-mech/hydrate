import os

import numpy as np

from zml import Dfn2
from zmlx.geometry.point_distance import point_distance
from zmlx.ptree.array import array
from zmlx.ptree.box import box2
from zmlx.ptree.ptree import PTree, as_ptree


def dfn2(pt):
    """
    从ptree中读取数据，并创建二维的dfn
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):
        fname = pt.find(pt.data)
        if os.path.isfile(fname):  # 尝试读取文件
            return np.loadtxt(fname, dtype=float).tolist()

    if isinstance(pt.data, list):
        fractures = []
        for item in pt.data:
            fractures = fractures + dfn2(as_ptree(item, path=pt.path))
        return fractures

    p21 = pt('p21', doc='The length of fracture in 1m^2')
    if p21 is None:
        print('p21 is None')
        return []

    assert p21 >= 0

    box = box2(pt['box'])
    assert len(box) == 4
    if abs(box[0] - box[2]) * abs(box[1] - box[3]) < 1.0e-10:
        print('area too small')
        return []

    angles = array(pt['angles'])
    if angles is None:
        print('angles not set')
        return []
    assert len(angles) > 0

    lengths = array(pt['lengths'])
    if lengths is None:
        print('lengths not set')
        return []

    lengths = [x for x in lengths if x > 0]
    if len(lengths) == 0:
        print('lengths are not positive')
        return []

    l_min = pt('l_min', doc='The minimum distance between fractures')
    if l_min is None:
        l_min = point_distance(box[0:2], box[2:4]) * 0.001

    buf = Dfn2()
    buf.range = box
    buf.add_frac(angles=angles, lengths=lengths, p21=p21, l_min=l_min)

    return buf.get_fractures()


def test():
    pt = PTree()
    pt.data = [
        {
            "p21": 1,
            "box": "0 0 10 10",
            "angles": 0,
            "lengths": "np.linspace(5,10,100)"
        },
        {
            "p21": 1,
            "box": "0 0 10 10",
            "angles": 1,
            "lengths": "np.linspace(5,10,100)"
        }]
    for f in dfn2(pt):
        print(f)


if __name__ == '__main__':
    test()
