import math

from zmlx.seepage_mesh.cube import create_cube


def create_cylinder(x=(0, 1, 2), r=(0, 1, 2)):
    """
    创建一个极坐标下的圆柱体的网格。其中圆柱体的对称轴为x轴。
    cell的y坐标为r。cell的z坐标为0.
    """
    assert x is not None and r is not None
    assert len(x) >= 2 and len(r) >= 2
    assert r[0] >= 0
    # Moreover, both x and r should be sorted from small to big
    # (this will be checked in function 'create_cube_seepage_mesh')

    rmax = r[-1]
    perimeter = 2.0 * math.pi * rmax
    mesh = create_cube(x, r, (-perimeter * 0.5, perimeter * 0.5))

    for cell in mesh.cells:
        (x, y, z) = cell.pos
        assert 0 < y < rmax
        cell.vol *= (y / rmax)

    for face in mesh.faces:
        (i0, i1) = face.link
        (x0, y0, _) = mesh.get_cell(i0).pos
        (x1, y1, _) = mesh.get_cell(i1).pos
        y = (y0 + y1) / 2
        assert 0 < y < rmax
        face.area *= (y / rmax)

    return mesh
