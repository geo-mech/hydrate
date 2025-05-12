"""
处理三角形网格相关的算法
"""
from scipy.spatial import Delaunay

from zml import Mesh3, np


def get_triangles(nodes):
    """
    给定二维点列表，返回由点索引构成的所有非退化三角形
    (每个三角形由三个点索引组成，从0开始计数)

    Args:
        nodes: 二维点列表，格式 [(x0,y0), (x1,y1), ...]

    Returns:
        三角形列表，格式 [[i,j,k], ...]，其中i,j,k为点索引
    """
    if len(nodes) < 3:
        return []

    points_array = np.array(nodes)

    try:
        tri = Delaunay(points_array)
    except:
        return []

    triangles = []
    for simplex in tri.simplices:
        # 获取三个点坐标
        a, b, c = points_array[simplex]

        # 计算向量叉积判断共线性
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) < 1e-10:  # 浮点数容差处理
            continue

        # 转换为Python原生int类型
        triangles.append([round(i) for i in simplex])

    return triangles


def layered_triangles(x_min, x_max, nx, y_min, y_max, ny, as_mesh=False):
    """
    在x_min <= x <= x_max, y_min <= y <= y_max的区域内，建立三角形网格.
    除了左右两侧的三角形(为直角三角形)，其它的三角形都是等腰三角形。
    在x方向，等腰三角形的底边长度乘以nx等于x_max - x_min.
    在y方向，等腰三角形的高乘以ny等于y_max - y_min.

    Args:
        as_mesh: 作为Mesh3对象返回，还是作为faces和nodes返回
        x_min: x坐标的最小值
        x_max: x坐标的最大值
        nx: x方向的三角形个数
        y_min: y坐标的最小值
        y_max: y坐标的最大值
        ny: y方向的三角形个数

    Returns:
        faces (list): 各个三角形的顶点的索引 (从0开始编号)
        nodes (list): 各个顶点的x, y坐标
    """

    dx = (x_max - x_min) / nx
    x1 = np.linspace(x_min, x_max, nx + 1)
    x2 = np.linspace(x_min - dx / 2, x_max + dx / 2, nx + 2)
    x2[0] = x_min
    x2[-1] = x_max

    nodes = []
    idx = 0
    for y in np.linspace(y_min, y_max, ny + 1):
        if idx % 2 == 0:
            p = [(x, y) for x in x1]
        else:
            p = [(x, y) for x in x2]
        idx += 1
        nodes.extend(p)

    faces = get_triangles(nodes)
    if as_mesh:
        return mesh3_from_triangles(faces, nodes)
    else:
        return faces, nodes


def mesh3_from_triangles(faces, nodes, ibeg=0):
    """
    根据三角形和顶点的索引，生成Mesh3对象.
    Args:
        faces: 各个三角形的顶点的索引 (从ibeg开始编号)
        nodes: 各个顶点的x, y坐标
        ibeg: 在faces中的索引的起始值

    Returns:
        Mesh3对象

    """
    mesh = Mesh3()

    for node in nodes:
        assert len(node) > 0
        pos = []
        for i in range(3):
            if i < len(node):
                pos.append(node[i])
            else:
                pos.append(0)
        mesh.add_node(*pos)

    for face in faces:
        if len(face) == 3:
            nodes = [round(x - ibeg) for x in face]
            l01 = mesh.add_link(nodes=[nodes[0], nodes[1]])
            l12 = mesh.add_link(nodes=[nodes[1], nodes[2]])
            l20 = mesh.add_link(nodes=[nodes[2], nodes[0]])
            mesh.add_face(links=[l01, l12, l20])

    return mesh


def test():
    """
    测试函数
    """
    from zmlx import trimesh
    faces, nodes = layered_triangles(
        0, 1, 10,
        0, 1, 10)
    print(mesh3_from_triangles(faces, nodes))
    trimesh(faces, nodes, gui_mode=True)


if __name__ == '__main__':
    test()
