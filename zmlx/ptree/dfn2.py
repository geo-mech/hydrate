from zmlx.ptree.box import box2
from zmlx.ptree.array import array
from zmlx.ptree.ptree import PTree
from zml import Dfn2
import warnings
from zmlx.geometry.point_distance import point_distance


def dfn2(pt, p21=0.0, box=None, angles=None, lengths=None, l_min=None):
    """
    从ptree中读取数据，并创建二维的dfn
    """
    assert isinstance(pt, PTree)

    p21 = pt('p21', default=p21, doc='The length of fracture in unit area')
    if p21 <= 0:
        warnings.warn('p21 <= 0')
        return []

    box = box2(pt, default=box)
    assert len(box) == 4
    if abs(box[0] - box[2]) * abs(box[1] - box[3]) < 1.0e-10:
        warnings.warn('area too small')
        return []

    text = ' '.join([str(x) for x in angles]) if angles is not None else ''
    angles = array(pt.child('angles'), text=text)
    if angles is None:
        warnings.warn('angles not set')
        return []
    assert len(angles) > 0

    text = ' '.join([str(x) for x in lengths]) if lengths is not None else ''
    lengths = array(pt.child('lengths'), text=text)
    if lengths is None:
        warnings.warn('lengths not set')
        return []

    lengths = [x for x in lengths if x > 0]
    if len(lengths) == 0:
        warnings.warn('lengths are not positive')
        return []

    l_min = pt('l_min', default=l_min if l_min is not None else point_distance(box[0:3], box[3:6]) * 0.001,
               doc='The minimum distance between fractures')

    buf = Dfn2()
    buf.range = box
    buf.add_frac(angles=angles, lengths=lengths, p21=p21, l_min=l_min)

    return buf.get_fractures()


def test():
    from zmlx.filesys.opath import opath
    from zmlx.ptree import json_file
    print(dfn2(pt=json_file(opath('dfn2.json'))))


if __name__ == '__main__':
    test()
