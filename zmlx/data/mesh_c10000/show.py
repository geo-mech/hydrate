import os


def test():
    import numpy as np
    from zmlx.plt import show_trimesh as trimesh
    folder = os.path.dirname(__file__)
    triangles = np.loadtxt(os.path.join(folder, "tri"), dtype=int)
    triangles -= 1
    points = np.loadtxt(os.path.join(folder, "xy"), dtype=float)

    # 绘制三角形网格
    trimesh(triangles=triangles, points=points)


if __name__ == '__main__':
    test()
