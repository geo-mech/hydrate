from zmlx.ptree.box import box3
from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree
import warnings
from zmlx.geometry.dfn_v3 import from_segs
from zmlx.ptree.dfn2 import dfn2


def dfn_v3(pt, p21=0.0, box=None, angles=None, lengths=None, l_min=None, heights=None, set_n=0):
    """
    创建一组dfn_v3
    """
    assert isinstance(pt, PTree)

    set_n = pt('set_n', default=set_n, doc='The count of fracture sets')
    if set_n > 0:
        fractures = []
        for idx in range(set_n):
            fractures = fractures + dfn_v3(pt=pt.child(f'set_{idx}'), p21=p21,
                                           box=box, angles=angles, lengths=lengths,
                                           l_min=l_min, heights=heights)
        return fractures

    box = box3(pt, default=box)
    assert len(box) == 6

    if abs(box[0] - box[3]) * abs(box[1] - box[4]) * abs(box[2] - box[5]) < 1.0e-15:
        warnings.warn('volume too small')
        return []

    segs = dfn2(pt, p21=p21, box=[box[0], box[1], box[3], box[4]],
                angles=angles, lengths=lengths, l_min=l_min)

    if len(segs) == 0:
        warnings.warn('no segments')
        return []

    text = ' '.join([str(x) for x in heights]) if heights is not None else ''
    heights = array(pt.child('heights'), text=text)
    if heights is None:
        warnings.warn('heights not set')
        return []
    assert len(heights) > 0

    return from_segs(segs=segs, z_min=box[2], z_max=box[5], heights=heights)


def test():
    from zmlx.filesys.opath import opath
    from zmlx.ptree import json_file
    for f in dfn_v3(pt=json_file(opath('dfn2.json'))):
        print(f)


if __name__ == '__main__':
    test()
