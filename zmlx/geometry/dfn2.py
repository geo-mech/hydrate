from zml import Dfn2
from zmlx.alg.linspace import linspace
from zmlx.geometry.point_distance import point_distance


def dfn2(data=None, **opt):
    """
    创建二维的dfn. 返回一个list，此list的每一个元素都是长度为4的list

    since 24-05-05
    """
    if data is not None:
        fractures = []
        for item in data:
            kw = opt.copy()
            kw.update(item)
            fractures = fractures + dfn2(**kw)
        return fractures

    xr, yr, p21 = opt.get('xr'), opt.get('yr'), opt.get('p21')
    l_min = opt.get('l_min')
    angles, lengths = opt.get('angles'), opt.get('lengths')

    if angles is None:
        ar = opt.get('ar')  # 角度的范围
        if ar is not None:
            angles = linspace(ar[0], ar[1], 100)

    if lengths is None:
        lr = opt.get('lr')
        if lr is not None:
            lengths = linspace(lr[0], lr[1], 100)

    if p21 is None or xr is None or yr is None or angles is None or lengths is None:
        return []

    assert len(xr) == 2 and len(yr) == 2

    if p21 <= 0:
        return []

    if xr[0] >= xr[1] or yr[0] >= yr[1]:
        return []

    lengths = [x for x in lengths if x > 0]

    if len(angles) == 0 or len(lengths) == 0:
        return []

    if l_min is None:
        l_min = point_distance((xr[0], yr[0]), (xr[1], yr[1])) * 0.001

    buf = Dfn2()
    buf.range = [xr[0], yr[0], xr[1], yr[1]]
    buf.add_frac(angles=angles, lengths=lengths, p21=p21, l_min=l_min)

    return buf.get_fractures()


def test():
    import numpy as np
    data = [
        {
            "p21": 1,
            "angles": [0],
            "lengths": np.linspace(5, 10, 100)
        },
        {
            "p21": 1,
            "angles": [1],
            "lengths": np.linspace(5, 10, 100)
        }]
    for f in dfn2(data, xr=[0, 10], yr=[0, 10]):
        print(f)


if __name__ == '__main__':
    test()
