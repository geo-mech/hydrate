"""
竖直方向的圆柱网格.
"""
import numpy as np
from zmlx.seepage_mesh.cylinder import create_cylinder
from zml import SeepageMesh


def create(z=(0, 1, 2), r=(0, 1, 2)):
    """
    创建一个竖直方向的圆柱坐标.
    """
    mesh = create_cylinder(x=z, r=r)  # 此时是躺着的一个模型.

    for cell in mesh.cells:  # 交换坐标
        assert isinstance(cell, SeepageMesh.Cell)
        x, y, z = cell.pos
        cell.pos = [y, z, x]

    # 返回最终的mesh
    return mesh


def create_hydrate_res(z_bottom, z0, z1, z_top, r_max, grid):
    """
    创建用于水合物开发的储层网格模型。在水合物层进行加密.
        其中grid为网格的最小间距.
        grid*3为网格的最大的间距.
    """
    vr = np.linspace(0, r_max, max(round(r_max / grid), 1) + 1)
    vz0 = np.linspace(z_bottom, z0,
                      max(round((z0 - z_bottom) / (grid * 3)), 1) + 1
                      )
    vz1 = np.linspace(z0, z1,
                      max(round((z1 - z0) / grid), 1) + 1
                      )
    vz2 = np.linspace(z1, z_top,
                      max(round((z_top - z1) / (grid * 3)), 1) + 1
                      )
    vz = np.concatenate((vz0, vz1[1:], vz2[1:]))
    return create(z=vz, r=vr)  # 创建mesh


if __name__ == '__main__':
    print(create_hydrate_res(z_bottom=-100, z0=-70, z1=-30, z_top=0, r_max=60, grid=2))
