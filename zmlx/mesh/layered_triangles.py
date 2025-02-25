import numpy as np
from zmlx.mesh.get_triangles import get_triangles


def layered_triangles(x_min, x_max, nx, y_min, y_max, ny):
    """
    在x_min <= x <= x_max, y_min <= y <= y_max的区域内，建立三角形网格.
    除了左右两侧的三角形(为直角三角形)，其它的三角形都是等腰三角形。
    在x方向，等腰三角形的底边长度乘以nx等于x_max - x_min.
    在y方向，等腰三角形的高乘以ny等于y_max - y_min.

    Args:
        x_min: x坐标的最小值
        x_max: x坐标的最大值
        nx: x方向的三角形个数
        y_min: y坐标的最小值
        y_max: y坐标的最大值
        ny: y方向的三角形个数

    Returns:
        faces (list): 各个三角形的顶点的索引 (从0开始编号)
        vertexes (list): 各个顶点的x, y坐标
    """

    dx = (x_max - x_min) / nx
    x1 = np.linspace(x_min, x_max, nx + 1)
    x2 = np.linspace(x_min-dx/2, x_max+dx/2, nx + 2)
    x2[0] = x_min
    x2[-1] = x_max

    vertexes = []
    idx = 0
    for y in np.linspace(y_min, y_max, ny+1):
        if idx % 2 == 0:
            p = [(x, y) for x in x1]
        else:
            p = [(x, y) for x in x2]
        idx += 1
        vertexes.extend(p)

    faces = get_triangles(vertexes)
    return faces, vertexes


def test():
    from zmlx.plt.trimesh import trimesh
    faces, vertexes = layered_triangles(
        0, 1, 10,
        0, 1, 10)
    trimesh(faces, vertexes, gui_mode=True)


if __name__ == '__main__':
    test()
