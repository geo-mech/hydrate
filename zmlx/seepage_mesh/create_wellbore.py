import numpy as np
from scipy.interpolate import interp1d

from zml import SeepageMesh
from zmlx.geometry.point_distance import point_distance


def create_wellbore(trajectory, length=1.0, area=0.01):
    """
    创建井筒的Mesh，其中trajectory为井筒的轨迹，
    length为每一个单元的长度，
    area为井筒的横截面积
    """
    # 计算轨迹上各个点距离起点的距离
    assert len(trajectory) >= 2

    vl = [0]
    vx = [trajectory[0][0]]
    vy = [trajectory[0][1]]
    vz = [trajectory[0][2]]

    for idx in range(1, len(trajectory)):
        p = trajectory[idx]
        vl.append(vl[-1] + point_distance(p, trajectory[idx - 1]))
        vx.append(p[0])
        vy.append(p[1])
        vz.append(p[2])

    # 新的节点的数量
    count = round(vl[-1] / length) + 1
    assert count >= 3
    length = vl[-1] / (count - 1)  # 每一个单元的长度

    # 在长度维度上的插值点
    lq = np.linspace(vl[0], vl[-1], count)

    # 插值，寻找节点
    f = interp1d(vl, vx)
    vx = f(lq)

    f = interp1d(vl, vy)
    vy = f(lq)

    f = interp1d(vl, vz)
    vz = f(lq)

    # 沿着井筒的轨迹来建立模型.
    mesh = SeepageMesh()

    # 创建代表井筒的网格
    for idx in range(len(vx)):
        x, y, z = vx[idx], vy[idx], vz[idx]
        # 代表井筒的单元
        c = mesh.add_cell()
        c.pos = [x, y, z]
        c.vol = area * length
        if idx > 0:
            f = mesh.add_face(c, mesh.get_cell(idx - 1))
            f.area = area
            f.length = length

    return mesh


def test_1():
    trajectory = [[0, 0, 0], [10, 0, 0], [10.1, 10, 0]]
    mesh = create_wellbore(trajectory)
    print(mesh)
    for cell in mesh.cells:
        print(cell.pos)


if __name__ == '__main__':
    test_1()
