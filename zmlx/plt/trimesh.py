from zmlx.data.trimesh_test import generate_test_mesh
from zmlx.plt.dfn2 import add_dfn2


def get_edges(triangles, points):
    edges = set()
    for tri in triangles:
        assert len(tri) == 3, f'The size of tri must be 3, but got: ({tri})'
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            if a > b:
                a, b = b, a
            edges.add((a, b))
    return [[points[a][0], points[a][1], points[b][0], points[b][1]] for a, b in edges]


def add_trimesh(ax, triangles, points, **opts):
    add_dfn2(ax, get_edges(triangles, points), **opts)


def trimesh(triangles, points, **opts):
    """
    调用plot，使用Matplotlib绘制二维三角形网格.

    Args:
        triangles: 三角形的索引，形状为(N, 3). 或者是一个list，且list的每一个元素的长度都是3
        points: 顶点坐标，形状为(N, 2). 或者是一个list，且list的每一个元素的长度都是2
        **opts: 传递给plot的参数，主要包括:
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)

    Note:
        此函数主要用于测试显示二维三角形网格的结构，类似与Matlab的trimesh函数，主要画出
        三角形的边，并且为了显示得更加清晰，边的颜色是随机的。
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    default_opts = dict(
        aspect='equal', linewidth=1.0,
        xlabel='x / m', ylabel='y / m', title='Triangle Mesh', tight_layout=True)
    opts = {**default_opts, **opts}

    plot(add_axes2, add_trimesh, triangles, points, **opts)


def test():
    # 生成测试网格
    triangles, points = generate_test_mesh()
    # 绘制三角形网格
    trimesh(triangles=triangles, points=points)


if __name__ == '__main__':
    test()
