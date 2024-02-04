import copy

from zmlx.geometry.dfn_v3 import from_segs, remove_small
from zmlx.ptree.array import array
from zmlx.ptree.box import box3
from zmlx.ptree.dfn2 import dfn2
from zmlx.ptree.ptree import PTree, as_ptree


def dfn_v3(pt, box=None):
    """
    创建一组dfn_v3
    """
    assert isinstance(pt, PTree)

    if isinstance(pt.data, str):
        data = array(pt)
        if data is not None:
            return data.tolist()

    if isinstance(pt.data, list):
        fractures = []
        for item in pt.data:
            fractures = fractures + dfn_v3(as_ptree(copy.deepcopy(item), path=pt.path), box=box)
        return fractures

    if box is None:
        box = box3(pt['box'])

    assert len(box) == 6

    if abs(box[0] - box[3]) * abs(box[1] - box[4]) * abs(box[2] - box[5]) < 1.0e-15:
        print('volume too small')
        return []

    segs = dfn2(pt, box=[box[0], box[1], box[3], box[4]])

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
            "p21": 1.0,
            "angles": "np.linspace(0, 0.4, 10)",
            "lengths": "np.linspace(5, 10, 100)",
            "heights": "np.linspace(5,10,100)",
            "remove_small": True
        },
        {
            "p21": 1.0,
            "angles": "np.linspace(1, 1.4, 10)",
            "lengths": "np.linspace(5, 10, 100)",
            "heights": "np.linspace(5,10,100)",
            "remove_small": True
        }
    ]
    fractures = dfn_v3(pt, box=[0, 0, 0, 30, 30, 30])
    for f in fractures:
        print(f)
    print(len(fractures))


if __name__ == '__main__':
    test()
