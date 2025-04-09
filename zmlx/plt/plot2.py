"""
基于Matplotlib的二维绘图
"""
from zmlx.plt.fig2 import plot2

version = 250401


def test_1():
    """
    测试
    """
    import matplotlib.tri as mtri
    try:
        import numpy as np
    except ImportError:
        np = None

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5])
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x)
    d1 = dict(
        name='tricontourf',
        kwds=dict(triangulation=triang, z=z, levels=30),
        has_colorbar=True)

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5]) + 3
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x) + 3
    d2 = dict(
        name='tricontourf',
        kwds=dict(triangulation=triang, z=z, levels=10))

    x = np.linspace(0, 5, 100)
    y = np.sin(x)
    d3 = dict(
        name='plot',
        args=[x, y],
        kwds=dict(c=(1, 0, 0, 0.5))
    )

    x = np.linspace(0, 5, 100)
    y = np.cos(x)
    d4 = dict(
        name='plot',
        args=[x, y],
        kwds=dict(c='r', linewidth=0.1)
    )

    plot2(data=[d1, d2, d3, d4], xlabel='x', ylabel='y')


if __name__ == '__main__':
    test_1()
