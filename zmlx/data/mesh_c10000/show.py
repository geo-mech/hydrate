import os

from zmlx.plt.trimesh import trimesh


def test():
    import numpy as np

    folder = os.path.dirname(__file__)
    triangles = np.loadtxt(os.path.join(folder, "tri"), dtype=int)
    triangles -= 1
    points = np.loadtxt(os.path.join(folder, "xy"), dtype=float)

    # 绘制三角形网格
    trimesh(triangles=triangles, points=points)


if __name__ == '__main__':
    test()
