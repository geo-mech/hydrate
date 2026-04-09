"""
创建圆柱形状的渗流网格.
"""
import math

from zmlx.seepage_mesh.cube import create_cube


def sort_and_deduplicate(arr):
    """
    对列表进行排序并去除重复元素

    Args:
        arr: 要处理的列表

    Returns:
        list: 从小到大排序且无重复元素的新列表
    """
    if not arr:
        return []

    # 使用集合去重，然后排序
    return sorted(set(arr))


def create_cylinder(x=(0, 1, 2), r=(0, 1, 2)):
    """
    创建一个极坐标下的圆柱体的网格。
    其中圆柱体的对称轴为x轴。cell的y坐标为r。cell的z坐标为0.
    """
    x = sort_and_deduplicate(x)
    r = sort_and_deduplicate(r)

    assert len(x) >= 2 and len(r) >= 2
    assert r[0] >= 0

    r_max = r[-1]
    perimeter = 2.0 * math.pi * r_max
    mesh = create_cube(x, r, (-perimeter * 0.5, perimeter * 0.5))

    for cell in mesh.cells:
        (x, y, z) = cell.pos
        assert 0 < y < r_max
        cell.vol *= (y / r_max)

    for face in mesh.faces:
        (i0, i1) = face.link
        (x0, y0, _) = mesh.get_cell(i0).pos
        (x1, y1, _) = mesh.get_cell(i1).pos
        y = (y0 + y1) / 2
        assert 0 < y < r_max
        face.area *= (y / r_max)

    return mesh


def test_1():
    m = create_cylinder(x=(0, 1, 2), r=(0, 1, 2))
    print(m)
    print(math.pi * 2 * 2 * 2)


def create_vertical_cylinder(z=(0, 1, 2), r=(0, 1, 2)):
    """
    创建纵向的圆柱
    """
    mesh = create_cylinder(x=z, r=r)

    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = [y, z, x]

    return mesh


def test_2():
    m = create_vertical_cylinder(z=(0, 1, 2), r=(0, 1, 2))
    print(m)
    print(math.pi * 2 * 2 * 2)


if __name__ == '__main__':
    test_2()
