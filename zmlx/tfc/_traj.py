"""
处理曲线在Seepage模型中留下的轨迹。
    最后检查：2026-6-27
"""
from typing import List, Union, Tuple

from zmlx.exts import Seepage, SeepageMesh


def get_cells_along_seg(
        p0: Union[List, Tuple], p1: Union[List, Tuple],
        model: Union[Seepage, SeepageMesh]
) -> List[int]:
    """
    返回沿着给定线段(segment)的所有的Cell的索引
    """
    assert len(p0) == 3 and len(p1) == 3, f"p0: {p0}, p1: {p1}. Both must be 3D."
    c0 = model.get_nearest_cell(pos=p0)  # pos的某一个或者多个维度可以是None，表示这个维度不参与计算
    c1 = model.get_nearest_cell(pos=p1)
    if c0 is None or c1 is None:
        return []

    if c0.index == c1.index:
        return [c0.index]

    # 中心点
    p2 = [None if p0[i] is None or p1[i] is None else (p0[i] + p1[i]) / 2 for i in range(3)]
    c2 = model.get_nearest_cell(pos=p2)
    assert c2 is not None

    if c2.index == c0.index or c2.index == c1.index:  # 此时，节点密度已经足够，直接返回
        return [c0.index, c1.index]
    else:  # 此时，细分为两段来递归地处理
        v0 = get_cells_along_seg(p0, p2, model=model)
        v1 = get_cells_along_seg(p2, p1, model=model)
        assert len(v0) > 0 and len(v1) > 0 and v0[-1] == v1[0]
        res = v0 + v1[1:]
        for i in range(len(res) - 1):
            assert res[i + 1] != res[i]
        return res


def get_cells_along(
        points: List[Union[List, Tuple]],
        model: Union[Seepage, SeepageMesh]
) -> List[int]:
    """
    返回沿着给轨迹(由多个points组成)的所有的Cell的索引
    Args:
        points: 多个点的坐标，定义一个三维的轨迹
        model: Seepage模型

    Returns:
        沿着给定轨迹的所有的Cell的索引
    """
    if len(points) == 0:
        return []
    elif len(points) == 1:
        return get_cells_along_seg(points[0], points[0], model=model)  # 正常返回一个Cell的索引
    else:
        res = []
        for index in range(len(points) - 1):
            vi = get_cells_along_seg(
                points[index], points[index + 1], model=model)
            if len(res) == 0:
                res = vi
            else:
                assert res[-1] == vi[0], f"res[-1]: {res[-1]}, vi[0]: {vi[0]}"  # 确保两个Cell的索引是连续的
                res.extend(vi[1:])
        return res


def test_1():
    import numpy as np
    model = SeepageMesh()
    for x in np.linspace(0, 10, 20):
        for y in np.linspace(0, 10, 20):
            c = model.add_cell()
            c.pos = [x, y, 0]

    vi = get_cells_along([[0, 0, None], [3, 5, None], [5, 5, None]], model=model)
    for i in vi:
        c = model.get_cell(i)
        assert c is not None
        print(c.pos)


if __name__ == '__main__':
    test_1()
