from zml import Dfn2
from zmlx.alg.utils import linspace
from zmlx.geometry.utils import point_distance


def dfn2(data=None, *, xr=None, yr=None, p21=None, l_min=None, angles=None,
         lengths=None, ar=None, lr=None, **ignores):
    """
    创建二维的dfn. 返回一个list，此list的每一个元素都是长度为4的list (格式为 x0  y0  x1  y1).

    since 24-05-05
    """
    if len(ignores) > 0:
        print(f'The following parameters are ignored in dfn2: {ignores.keys()}')

    if data is not None:
        fractures = []
        for item in data:
            kw = dict(xr=xr, yr=yr, p21=p21, l_min=l_min, angles=angles,
                      lengths=lengths, ar=ar, lr=lr)
            kw.update(item)
            fractures = fractures + dfn2(**kw)
        return fractures

    if angles is None:
        if ar is not None:
            angles = linspace(ar[0], ar[1], 100)

    if lengths is None:
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


def get_length(fracture):
    """
    获取裂缝的长度。 fracture是一个长度为4的list，格式为 x0  y0  x1  y1
    """
    return point_distance((fracture[0], fracture[1]),
                          (fracture[2], fracture[3]))


def get_center(fracture):
    """
    获取裂缝的中心。 fracture是一个长度为4的list，格式为 x0  y0  x1  y1
    """
    return [(fracture[0] + fracture[2]) / 2, (fracture[1] + fracture[3]) / 2]


def get_total_length(fractures):
    """
    计算所有的裂缝的总的长度
    """
    total = 0.0
    for frac in fractures:
        total += get_length(frac)
    return total


def get_avg_length(fractures):
    """
    计算所有裂缝长度的平均值

    参数：
    fractures - 裂缝列表，每个元素是[x0, y0, x1, y1]格式的裂缝端点坐标

    返回：
    所有裂缝的平均长度（浮点数）
    """
    if len(fractures) == 0:
        return 0.0
    else:
        return get_total_length(fractures) / len(fractures)


def test():
    data = [
        dict(p21=1, angles=[0], lr=[5, 10]),
        dict(p21=1, angles=[1], lr=[5, 10]),
    ]
    fractures = dfn2(data, xr=[0, 10], yr=[0, 10])
    print(f'average length = {get_avg_length(fractures)}')
    from zmlx.plt.fig2 import show_dfn2
    show_dfn2(fractures)


if __name__ == '__main__':
    test()
