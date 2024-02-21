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


def create_option(p21=0.0, a0=-0.5, a1=0.5, l0=10.0, l1=20.0, h0=5.0, h1=10.0, remove_small=True, l_min=0.2):
    """
    生成一个创建创建dfn的参数选项
    """
    return [
        {
            'p21': p21 / 2,
            'angles': f'np.linspace({a0}, {a1}, 50)',
            'lengths': f'np.linspace({l0}, {l1}, 50)',
            'l_min': l_min,
            'heights': f'np.linspace({h0}, {h1}, 50)',
            'remove_small': remove_small
        }
    ]


def test():
    pt = PTree()
    pt.data = create_option(p21=1.0, a0=0, a1=0.4, l0=5, l1=10, h0=5, h1=10, remove_small=True) + create_option(
        p21=1.0, a0=1, a1=1.4, l0=5, l1=10, h0=5, h1=10, remove_small=True)
    fractures = dfn_v3(pt, box=[0, 0, 0, 30, 30, 30])
    for f in fractures:
        print(f)
    print(len(fractures))


if __name__ == '__main__':
    test()
