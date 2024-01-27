import numpy as np

from zml import SeepageMesh

# 创建立方体的渗流网格
create = SeepageMesh.create_cube


def create_xyz(*, x_min, dx, x_max, y_min, dy, y_max, z_min, dz, z_max):
    """
    创建三维网格（采用完全均匀的网格）
    """
    jx = max(round((x_max - x_min) / dx), 1) + 1
    jy = max(round((y_max - y_min) / dy), 1) + 1
    jz = max(round((z_max - z_min) / dz), 1) + 1
    x = np.linspace(x_min, x_max, jx)
    y = np.linspace(y_min, y_max, jy)
    z = np.linspace(z_min, z_max, jz)
    return SeepageMesh.create_cube(x, y, z)


def create_xz(*, x_min, dx, x_max, z_min, dz, z_max, y_min, y_max):
    """
    创建xz平面内的二维的网格
    """
    return create_xyz(x_min=x_min, dx=dx, x_max=x_max, y_min=y_min, dy=1e20, y_max=y_max,
                      z_min=z_min, dz=dz, z_max=z_max)
