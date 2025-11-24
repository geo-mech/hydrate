from zmlx.base.zml import np
from zmlx.seepage_mesh.cube import create_cube


def create_xz(x_max, z_min, z_max, dx, dz, upper=0, lower=0):
    """
    创建一个具有上覆层和下伏层的二维网格

    参数:
    - x_max: x方向的最大值
    - z_min: z方向的最小值
    - z_max: z方向的最大值
    - dx: x方向的网格间距
    - dz: z方向的网格间距
    - upper: 上覆层的厚度
    - lower: 下伏层的厚度

    返回:
    - 一个二维网格

    注意:
    - 上覆层和下伏层的厚度不能超过总厚度的90%
    - x方向的网格数量必须在5到200之间
    """
    # 创建x
    assert x_max > 0
    jx = round(x_max / dx) + 1
    assert 5 <= jx <= 200
    vx = np.linspace(0, x_max, jx)

    # 创建z
    assert upper >= 0
    assert lower >= 0
    assert upper + lower < (z_max - z_min) * 0.9

    # 创建z方向的网格
    if lower > dz:
        jz = round(lower / (dz * 3)) + 1
        assert jz >= 2
        vz1 = np.linspace(
            z_min, z_min + lower, jz, endpoint=False).tolist()
        z0 = z_min + lower
    else:
        vz1 = []
        z0 = z_min

    if upper > dz:
        jz = round(upper / (dz * 3)) + 1
        assert jz >= 2
        vz3 = np.linspace(
            z_max, z_max - upper, jz, endpoint=False).tolist()
        vz3.reverse()
        z1 = z_max - upper
    else:
        vz3 = []
        z1 = z_max

    # 中间水合物层的网格
    jz = round((z1 - z0) / dz) + 1
    assert jz >= 2
    vz2 = np.linspace(z0, z1, jz).tolist()

    # 所有的z方向的网格节点
    vz = vz1 + vz2 + vz3  # z方向的节点

    return create_cube(x=vx, y=[-0.5, 0.5], z=vz)


if __name__ == '__main__':
    print(create_xz(
        x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
        lower=30))
