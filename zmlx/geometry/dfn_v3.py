import random

from zml import np
from zmlx.alg.utils import clamp, linspace
from zmlx.geometry.dfn2 import dfn2
from zmlx.geometry.rect_3d import from_v3
from zmlx.geometry.rect_v3 import intersected, get_area


def from_segs(segs, z_min, z_max, heights):
    """
    基于二维的裂缝，添加一个高度，创建三维的
    """
    assert len(heights) > 0
    assert z_min < z_max
    fractures = []

    for f2 in segs:
        x0, y0, x1, y1 = f2
        z = random.uniform(z_min, z_max)
        assert len(heights) >= 1
        h = heights[round(random.uniform(0, len(heights) - 1))]
        z0 = z - h / 2
        z1 = z + h / 2
        z0 = clamp(z0, z_min, z_max)
        z1 = clamp(z1, z_min, z_max)
        fractures.append([x0, y0, z0, x1, y1, z1])

    return fractures


def dfn_v3(data=None, **opt):
    """
    创建一个拟三维的DFN: 裂缝面都垂直于x-y平面.  返回的裂缝数据的格式为： x0, y0, z0, x1, y1, z1.

    since 24-05-05
    """
    if data is not None:
        fractures = []
        for item in data:
            kw = opt.copy()
            kw.update(item)
            fractures = fractures + dfn_v3(**kw)
        return fractures

    # z方向的范围和裂缝的高度分布
    zr, heights = opt.get('zr'), opt.get('heights')

    if heights is None:
        hr = opt.get('hr')
        if hr is not None:
            heights = linspace(hr[0], hr[1], 100)

    if zr is None or heights is None:
        return []

    assert len(zr) == 2
    if zr[0] >= zr[1]:
        return []

    if len(heights) <= 0:
        return []

    # 生成裂缝数据
    fractures = from_segs(dfn2(**opt), z_min=zr[0], z_max=zr[1],
                          heights=heights)

    if opt.get('remove_small', False):
        return remove_small(fractures)
    else:
        return fractures


def create_fractures(box=None, p21=None, angles=None, lengths=None,
                     heights=None, l_min=None):
    """
    创建一个拟三维的DFN: 裂缝面都垂直于x-y平面.  返回的裂缝数据的格式为： x0, y0, z0, x1, y1, z1
    --
    :param box: 坐标的范围，格式为: x_min, y_min, z_min, x_max, y_max, z_max
    :param p21: 在二维平面上裂缝的密度
    :param angles: 裂缝的角度
    :param lengths: 裂缝的长度
    :param heights: 裂缝的高度
    :param l_min: 裂缝允许的最近的距离
    :return: 三维裂缝数据，格式: x0, y0, z0, x1, y1, z1
    --
    创建时间:
        2023-5-3   by 张召彬
    """
    if box is None:
        box = [-50, -150, -25, 50, 150, 25]
    if p21 is None:
        p21 = 1
    if angles is None:
        angles = [0.0, 1.57]
    if lengths is None:
        lengths = linspace(10, 50, 100)
    if heights is None:
        heights = linspace(5, 25, 100)
    if l_min is None:
        l_min = 0.1

    assert len(box) == 6
    x_min, y_min, z_min, x_max, y_max, z_max = box

    return dfn_v3(xr=[x_min, x_max], yr=[y_min, y_max], zr=[z_min, z_max],
                  p21=p21, angles=angles,
                  lengths=lengths, heights=heights, l_min=l_min)


def remove_small(fractures):
    """
    删除那些非常小的裂缝，并且返回
    """
    if len(fractures) == 0:
        return []
    average_s = 0
    for f3 in fractures:
        average_s += get_area(f3)
    average_s /= len(fractures)

    temp = []
    for f3 in fractures:
        if get_area(f3) > average_s * 0.025:  # 抛弃那些特别小的裂缝
            temp.append(f3)
    return temp


def create_links(fractures):
    """
    寻找相互连通的裂缝组合
    """
    links = []
    for i0 in range(len(fractures)):
        a = fractures[i0]
        for i1 in range(i0 + 1, len(fractures)):
            b = fractures[i1]
            if intersected(a, b):
                links.append([i0, i1])
    return links


def save_c14(path, fractures):
    """
    保存为14列的数据，用于Matlab绘图
    """
    with open(path, 'w') as file:
        for x0, y0, z0, x1, y1, z1 in fractures:
            file.write(
                f'{x0} {x0} {x1} {x1} {y0} {y0} {y1} {y1} {z0} {z1} {z0} {z1} 0 0\n')


def __cen(x, y):
    """
    返回点x和y的中心点
    """
    return [(x[i] + y[i]) / 2 for i in range(3)]


def __sym(c, x):
    """
    返回x关于中心点x的对称点
    """
    return [c[i] * 2 - x[i] for i in range(3)]


def to_rc3(fractures):
    """
    将<多个>竖直的裂缝（用6个数字表示）修改为用9个数字（矩形中心坐标和两个相邻边的中心坐标）表示的三维矩形的形式
    """
    return from_v3(fractures, multiple=True)


def create_demo(heights=None):
    """
    创建一个用于计算测试的裂缝
    """
    fx = create_fractures(p21=0.3, angles=linspace(-0.2, 0.2, 100),
                          lengths=linspace(10, 20, 100), heights=heights)
    fy = create_fractures(p21=0.7, angles=linspace(1.57 - 0.2, 1.57 + 0.2, 100),
                          lengths=linspace(20, 40, 100), heights=heights)

    print(f'count of fx: {len(fx)}')
    print(f'count of fy: {len(fy)}')

    fractures = fx + fy
    print(f'count of fractures: {len(fractures)}')

    fractures = remove_small(fractures)
    print(f'count of fractures: {len(fractures)} (after remove small)')

    return fractures


def test_1():
    from zmlx.pg.show_rc3 import show_rc3
    import random
    rc3 = to_rc3(create_demo(heights=linspace(5, 10, 30)))
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(0, 1))
        alpha.append(random.uniform(0, 1) ** 3)
    show_rc3(rc3, color=color, alpha=alpha, caption='dfn_v3')


if __name__ == '__main__':
    np.savetxt('dfn_v3_demo.txt', to_rc3(create_demo()), fmt='%.3f')
