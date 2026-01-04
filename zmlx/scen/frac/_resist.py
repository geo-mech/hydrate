"""
评估流动阻力系数
"""

from typing import List, Tuple

from zmlx.exts import Seepage


def add_cell(model: Seepage, p: float, is_soft: bool = False):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        is_soft: 是否为软单元
        p: 单元的压力，Pa
    """
    c = model.add_cell().set_pore(p=1, v=1.0e7, dp=1, dv=0.5e7 if is_soft else 1.0e-3)
    c.fluid_number = 1
    assert 0 < p < 10.0, f'p {p} should be in range (0, 10.0)'
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0
    return c


def add_face(model: Seepage, i0: int, i1: int, resist: float):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        i0: 第一个单元的索引
        i1: 第二个单元的索引
        resist: 流动阻力系数. 假设流体粘度1，流量1的时候的阻力Pa
    """
    assert resist > 0, f'resist {resist} should be greater than 0'
    face = model.add_face(i0, i1)
    face.cond = 1.0 / resist
    return face


def get_fp(model: Seepage, index: int) -> float:
    cell = model.get_cell(index)
    assert cell is not None
    return cell.pre


def test_1():
    """
    测试add_cell和add_face
    """
    model = Seepage()
    add_cell(model, p=2, is_soft=True)
    add_cell(model, p=1, is_soft=False)
    add_cell(model, p=1, is_soft=False)
    add_cell(model, p=1, is_soft=True)
    add_face(model, 0, 1, 1.0)
    add_face(model, 1, 2, 1.0)
    add_face(model, 2, 3, 1.0)
    for i in range(10):
        model.iterate(dt=1)
        print(get_fp(model, 0), get_fp(model, 1), get_fp(model, 2), get_fp(model, 3))


# if __name__ == '__main__':
#     test_1()


def get_fv(model: Seepage, index: int) -> float:
    cell = model.get_cell(index)
    assert cell is not None
    return cell.fluid_vol


def get_resist(links: List[Tuple[int, int]], link_resists: List[float], start: int, ends: List[int]) -> List[float]:
    """
    评估从一个给定顶点，到其他顶点之间的流动阻力系数.
    """
    vertex_number = 0
    for i0, i1 in links:
        vertex_number = max(vertex_number, i0 + 1, i1 + 1)

    assert start < vertex_number
    assert all([i < vertex_number for i in ends]), f'ends {ends} are not in range {vertex_number}'

    ends_set = set(ends)
    assert start not in ends_set, f'start {start} is in ends {ends}'

    model = Seepage()
    while model.cell_number < vertex_number:
        idx = model.cell_number
        if idx == start:
            add_cell(model, p=2.0, is_soft=True)
        elif idx in ends_set:
            add_cell(model, p=1.0, is_soft=True)
        else:
            add_cell(model, p=1.5, is_soft=False)

    assert len(links) == len(link_resists), f'links {links} and link_resists {link_resists} have different lengths'
    resist_min = min(link_resists)
    assert resist_min > 0, f'resist min {resist_min} should be greater than 0'

    for i in range(len(links)):
        i0, i1 = links[i]
        assert i0 != i1
        add_face(model, i0, i1, resist=link_resists[i] / resist_min)

    # 备份ends初始时刻的流体体积
    end_fv0 = [get_fv(model, i) for i in ends]

    # 向前迭代1s
    dt = 1.0
    model.iterate(dt=dt)

    # 计算体积变化
    end_fv1 = [get_fv(model, i) for i in ends]
    end_resists = [resist_min / ((end_fv1[i] - end_fv0[i]) / dt) for i in range(len(ends))]

    return end_resists


def test_2():
    links: List[Tuple[int, int]] = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5)]
    link_resists: List[float] = [88, 1, 1, 1, 1]
    start: int = 1
    ends: List[int] = [0, 4]
    end_resists = get_resist(links, link_resists, start, ends)
    print(end_resists)


if __name__ == '__main__':
    test_2()
