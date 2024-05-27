import numpy as np

from zml import SeepageMesh


def create_cube(x=(-0.5, 0.5), y=(-0.5, 0.5), z=(-0.5, 0.5), boxes=None,
                ca_ix=None, ca_iy=None, ca_iz=None):
    """
    创建一个立方体网格的Mesh. 参数x、y、z分别为三个方向上网格节点的位置，应保证是从小到大
    排列好的。
        当给定ca_ix的时候，将设置cell的x方向的序号；
        当给定ca_iy的时候，将设置cell的y方向的序号；
        当给定ca_iz的时候，将设置cell的z方向的序号；
    其中:
        当boxes是一个list的时候，将会把各个Cell对应的box，
            格式为(x0, y0, z0, x1, y1, z1)附加到这个list里面，
        用以定义各个Cell的具体形状.
    """
    assert x is not None and y is not None and z is not None
    assert len(x) + len(y) + len(z) >= 6

    def is_sorted(vx):
        for i in range(len(vx) - 1):
            if vx[i] >= vx[i + 1]:
                return False
        return True

    assert is_sorted(x) and is_sorted(y) and is_sorted(z)

    jx = len(x) - 1
    jy = len(y) - 1
    jz = len(z) - 1
    assert jx > 0 and jy > 0 and jz > 0

    mesh = SeepageMesh()

    for ix in range(0, jx):
        dx = x[ix + 1] - x[ix]
        cx = x[ix] + dx / 2
        for iy in range(0, jy):
            dy = y[iy + 1] - y[iy]
            cy = y[iy] + dy / 2
            for iz in range(0, jz):
                dz = z[iz + 1] - z[iz]
                cz = z[iz] + dz / 2
                cell = mesh.add_cell()
                assert cell is not None
                # cell的位置和体积
                cell.pos = (cx, cy, cz)
                cell.vol = dx * dy * dz
                # 设置cell所处的行列的id
                if ca_ix is not None:
                    cell.set_attr(ca_ix, ix)
                if ca_iy is not None:
                    cell.set_attr(ca_iy, iy)
                if ca_iz is not None:
                    cell.set_attr(ca_iz, iz)
                # 设置属性，用以定义Cell的位置的范围.
                if boxes is not None:
                    boxes.append([cx - dx / 2,
                                  cy - dy / 2,
                                  cz - dz / 2,
                                  cx + dx / 2,
                                  cy + dy / 2,
                                  cz + dz / 2])

    def get_id(ix, iy, iz):
        """
        返回cell的全局的序号
        """
        return ix * (jy * jz) + iy * jz + iz

    cell_n = mesh.cell_number
    for ix in range(0, jx - 1):
        dx = (x[ix + 2] - x[ix]) / 2
        for iy in range(0, jy):
            dy = y[iy + 1] - y[iy]
            for iz in range(0, jz):
                dz = z[iz + 1] - z[iz]
                i0 = get_id(ix, iy, iz)
                i1 = get_id(ix + 1, iy, iz)
                assert i0 < cell_n and i1 < cell_n
                face = mesh.add_face(mesh.get_cell(i0),
                                     mesh.get_cell(i1))
                assert face is not None
                face.area = dy * dz
                face.length = dx

    for ix in range(0, jx):
        dx = x[ix + 1] - x[ix]
        for iy in range(0, jy - 1):
            dy = (y[iy + 2] - y[iy]) / 2
            for iz in range(0, jz):
                dz = z[iz + 1] - z[iz]
                i0 = get_id(ix, iy, iz)
                i1 = get_id(ix, iy + 1, iz)
                assert i0 < cell_n and i1 < cell_n
                face = mesh.add_face(mesh.get_cell(i0),
                                     mesh.get_cell(i1))
                assert face is not None
                face.area = dx * dz
                face.length = dy

    for ix in range(0, jx):
        dx = x[ix + 1] - x[ix]
        for iy in range(0, jy):
            dy = y[iy + 1] - y[iy]
            for iz in range(0, jz - 1):
                dz = (z[iz + 2] - z[iz]) / 2
                i0 = get_id(ix, iy, iz)
                i1 = get_id(ix, iy, iz + 1)
                assert i0 < cell_n and i1 < cell_n
                face = mesh.add_face(mesh.get_cell(i0),
                                     mesh.get_cell(i1))
                assert face is not None
                face.area = dx * dy
                face.length = dz

    return mesh


def create_xyz(*, x_min, dx, x_max, y_min, dy, y_max, z_min, dz, z_max,
               show_details=False, **kwargs):
    """
    创建三维网格（采用完全均匀的网格）
    """
    jx = max(round((x_max - x_min) / dx), 1) + 1
    jy = max(round((y_max - y_min) / dy), 1) + 1
    jz = max(round((z_max - z_min) / dz), 1) + 1

    x = np.linspace(x_min, x_max, jx)
    y = np.linspace(y_min, y_max, jy)
    z = np.linspace(z_min, z_max, jz)

    if show_details:
        print(f'x_min = {x_min}, x_max = {x_max}, jx = {jx}')
        print(f'y_min = {y_min}, y_max = {y_max}, jy = {jy}')
        print(f'z_min = {z_min}, z_max = {z_max}, jz = {jz}')

    return create_cube(x, y, z, **kwargs)


def create_xy(*, x_min, dx, x_max, y_min, dy, y_max, z_min, z_max,
              **kwargs):
    """
    创建xy平面内的二维的网格
    """
    return create_xyz(x_min=x_min, dx=dx, x_max=x_max,
                      y_min=y_min, dy=dy, y_max=y_max,
                      z_min=z_min, dz=1e20, z_max=z_max, **kwargs)


def create_xz(*, x_min, dx, x_max, z_min, dz, z_max, y_min, y_max,
              **kwargs):
    """
    创建xz平面内的二维的网格
    """
    return create_xyz(x_min=x_min, dx=dx, x_max=x_max,
                      y_min=y_min, dy=1e20, y_max=y_max,
                      z_min=z_min, dz=dz, z_max=z_max, **kwargs)
