import os

from zml import read_text, Mesh3
from zmlx.seepage_mesh.mesh3 import face_centered


def load_xy_data():
    """
    加载xy数据
    Returns:
        一个字符串，每一行包含一个点的坐标，格式为"x y"
    """
    return read_text(os.path.join(os.path.dirname(__file__), 'xy'))


def load_tri_data():
    """
    加载tri数据
    Returns:
        一个字符串，每一行包含一个三角形的三个顶点索引，格式为"i j k"
    """
    return read_text(os.path.join(os.path.dirname(__file__), 'tri'))


def load_triangles(tri_data=None, xy_data=None):
    """
    加载三角形数据
    Args:
        tri_data: 三角形数据，每一行包含一个三角形的三个顶点索引，格式为"i j k"
        xy_data: 点数据，每一行包含一个点的坐标，格式为"x y"
    Returns:
        一个列表，每个元素是一个三角形的三个顶点索引
    """
    if tri_data is None:
        tri_data = load_tri_data()
    if xy_data is None:
        xy_data = load_xy_data()

    x = []
    y = []

    for line in xy_data.splitlines():
        values = [float(s) for s in line.split()]
        if len(values) == 2:
            x.append(values[0])
            y.append(values[1])

    tri = []
    for line in tri_data.splitlines():
        values = [int(s) - 1 for s in line.split()]
        if len(values) == 3:
            tri.append(tuple(values))

    return tri, x, y


# 注意，在模块中，直接读取文件，会影响模块的加载速度
# 后续，这种方式会被移除。
# 后续，将采用函数的形式。
xy_data = load_xy_data()
tri_data = load_tri_data()
tri, x, y = load_triangles(tri_data, xy_data)


def get_mesh3(z=0):
    tri, x, y = load_triangles(tri_data, xy_data)
    mesh = Mesh3()

    for idx in range(len(x)):
        mesh.add_node(x[idx], y[idx], z=z)

    for t in tri:
        links = [mesh.add_link([mesh.get_node(t[i]), mesh.get_node(t[j])]) for
                 (i, j) in [(0, 1), (1, 2), (2, 0)]]
        mesh.add_face(links=links)

    return mesh


def get_face_centered_seepage_mesh(z=0, thick=1.0):
    mesh3 = get_mesh3(z=z)
    return face_centered(mesh=mesh3, thick=thick)


if __name__ == '__main__':
    print(get_face_centered_seepage_mesh())
