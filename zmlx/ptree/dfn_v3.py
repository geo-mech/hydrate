import os
import numpy as np
from zmlx.geometry.dfn_v3 import from_segs, remove_small
from zmlx.ptree.array import array
from zmlx.ptree.box import box3
from zmlx.ptree.dfn2 import dfn2
from zmlx.ptree.ptree import PTree, as_ptree


def dfn_v3(pt):
    """
    创建一组dfn_v3
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):
        fname = pt.find(pt.data)
        if os.path.isfile(fname):  # 尝试读取文件
            return np.loadtxt(fname, dtype=float).tolist()
        else:
            return []

    if isinstance(pt.data, list):
        fractures = []
        for item in pt.data:
            fractures = fractures + dfn_v3(as_ptree(item, path=pt.path))
        return fractures

    box = box3(pt['box'])
    assert len(box) == 6

    if abs(box[0] - box[3]) * abs(box[1] - box[4]) * abs(box[2] - box[5]) < 1.0e-15:
        print('volume too small')
        return []

    segs = dfn2(pt)

    if len(segs) == 0:
        print('no segments')
        return []

    heights = array(pt['heights'])
    if heights is None:
        print('heights not set')
        return []
    assert len(heights) > 0

    fractures = from_segs(segs=segs, z_min=box[2], z_max=box[5], heights=heights)
    if pt('remove_small', doc='Remove the small fractures'):
        return remove_small(fractures)
    else:
        return fractures


def test():
    pt = PTree()
    pt.data = [
        {
            "box": [0, 0, 0, 30, 30, 30],
            "p21": 1.0,
            "angles": "np.linspace(0, 0.4, 10)",
            "lengths": "np.linspace(5, 10, 100)",
            "heights": "np.linspace(5,10,100)",
            "remove_small": True
        },
        {
            "box": [0, 0, 0, 30, 30, 30],
            "p21": 1.0,
            "angles": "np.linspace(1, 1.4, 10)",
            "lengths": "np.linspace(5, 10, 100)",
            "heights": "np.linspace(5,10,100)",
            "remove_small": True
        }
    ]
    fractures = dfn_v3(pt)
    for f in fractures:
        print(f)
    print(len(fractures))


if __name__ == '__main__':
    test()
