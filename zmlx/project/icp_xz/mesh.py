from zmlx.seepage_mesh.cube import create_xz


def create_mesh(dx=None, dz=None):
    """
    建立mesh
    """

    if dx is None:
        dx = 0.3

    if dz is None:
        dz = 0.3

    # 创建mesh(注意，这里的z代表了竖直方向)
    #   包含了上下覆层各15米
    mesh = create_xz(x_min=0, dx=dx, x_max=15.0,
                     y_min=-1, y_max=0,
                     z_min=-30.0, dz=dz, z_max=30.0,
                     )
    return mesh


if __name__ == '__main__':
    print(create_mesh())

