from zml import Dfn2
from zmlx.alg.linspace import linspace
from zmlx.alg.clamp import clamp
import random
from zmlx.geometry.rect_v3 import intersected, get_area
from zmlx.geometry.rect_3d import from_v3
from zmlx.io.json_ex import ConfigFile


def create_fractures(box=None, p21=None, angles=None, lengths=None, heights=None, l_min=None):
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

    dfn2 = Dfn2()
    dfn2.range = (x_min, y_min, x_max, y_max)
    dfn2.add_frac(angles=angles, lengths=lengths,
                  p21=p21, l_min=l_min)

    fractures = []

    for f2 in dfn2.get_fractures():
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
            file.write(f'{x0} {x0} {x1} {x1} {y0} {y0} {y1} {y1} {z0} {z1} {z0} {z1} 0 0\n')


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
    return [from_v3(v3) for v3 in fractures]


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


def from_json_(json=None, box=None,
               p21=0.0, a_min=0.0, a_max=0.0, l_min=10.0, l_max=20.0, h_min=5.0, h_max=10.0):
    """
    根据配置创建一组裂缝
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            assert isinstance(json, str)
            json = ConfigFile(json)

    if box is None:
        box = [0, 0, 0, 1, 1, 1]

    if json is not None:
        box = json(key='box', default=box,
                   doc='The position range of the fractures')

    assert len(box) == 6
    x0, y0, z0, x1, y1, z1 = box

    assert x0 < x1
    assert y0 < y1
    assert z0 < z1

    if isinstance(json, ConfigFile):
        p21 = json(key='p21', default=p21, doc='the fracture density')

    assert 0.0 <= p21 < 2.0

    if p21 > 0:
        if isinstance(json, ConfigFile):
            a_min = json('a_min', default=a_min,
                         doc='The minimum angle between fracture and x axis')
            a_max = json('a_max', default=a_max,
                         doc='The maximum angle between fracture and x axis')
            l_min = json('l_min', default=l_min,
                         doc='The minimum fracture length')
            l_max = json('l_max', default=l_max,
                         doc='The maximum fracture length')
            h_min = json('h_min', default=h_min,
                         doc='The minimum fracture height')
            h_max = json('h_max', default=h_max,
                         doc='The maximum fracture height')
        return create_fractures(box=box, p21=p21, angles=linspace(a_min, a_max, 100),
                                lengths=linspace(l_min, l_max, 100),
                                heights=linspace(h_min, h_max, 100))
    else:
        return []


def from_json(json=None, count=0, box=None,
              p21=0.0, a_min=0.0, a_max=0.0, l_min=10.0, l_max=20.0, h_min=5.0, h_max=10.0):
    """
    根据给定的输入配置，来创建一个dfn
    """
    if json is not None:
        if not isinstance(json, ConfigFile):
            assert isinstance(json, str)
            json = ConfigFile(json)

    if json is not None:
        count = json(key='count',
                     default=0,
                     doc='The count of fracture sets')
    assert 0 <= count < 10

    if count == 0:
        return []

    fractures = []

    for i in range(count):
        temp = from_json_(
            json=json.child(f'set{i}', doc=f'the setting of fracture set {i}') if json is not None else None,
            box=box,
            p21=p21, a_min=a_min, a_max=a_max, l_min=l_min, l_max=l_max, h_min=h_min, h_max=h_max
        )
        fractures = fractures + temp

    fractures = remove_small(fractures)
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


def test_2():
    def xxx(fractures):
        """
        寻找相互连通的裂缝组合
        """
        from zml import Hf2Alg
        links = []
        for i0 in range(len(fractures)):
            a = fractures[i0]
            for i1 in range(i0 + 1, len(fractures)):
                b = fractures[i1]
                if Hf2Alg.rect_v3_intersected(a, b):
                    links.append([i0, i1])
        return links

    import timeit
    fractures = create_demo()
    t1 = timeit.default_timer()
    links = create_links(fractures)
    t2 = timeit.default_timer()
    print(f'count links = {len(links)}. time = {t2 - t1}')
    links = xxx(fractures)
    t3 = timeit.default_timer()
    print(f'count links = {len(links)}. time = {t3 - t2}')


def test_3():
    from zmlx.filesys.opath import opath
    fractures = from_json(opath('dfn_v3.json'))
    print(f'count of fractures = {len(fractures)}')


if __name__ == '__main__':
    test_3()
    # gui.execute(test, close_after_done=False)
