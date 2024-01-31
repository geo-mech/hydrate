from zml import SeepageMesh
import numpy as np


def create_mesh(width, height, dw, dh):
    """
    创建网格. 模型高度height，宽度width.
    """
    assert 15.0 <= width <= 500.0 and 100.0 <= height <= 500.0
    assert 0.5 <= dw <= 5.0
    assert 0.5 <= dh <= 5.0
    jx = round(width / dw)
    jz = round(height / dh)
    x = np.linspace(0, width, jx)
    y = [-0.5, 0.5]
    z = np.linspace(-height, 0, jz)
    return SeepageMesh.create_cube(x, y, z)


def create_cylinder(radius=300.0, depth=400.0, height=0.0, dr=1.0, dh=1.0, rc=0, hc=0, ratio=1.02,
                    dr_max=None, dh_max=None):
    """
    创建柱坐标网格.  (主要用于co2封存模拟). 其中：
        radius: 圆柱体的半径
        depth: 圆柱体的高度(在海底面以下的深度)
        height: 在海面以上的高度 (在海底面以上的深度. 注意，这里的网格，其主要的目的，是模拟出口边界)
        dr: 在半径方向上的(初始的)网格的大小
        dh: 在高度方向上的(初始的)网格的大小
        rc: 临界的半径(在这个范围内一直采用细网格)
        hc: 临界的高度(在这个范围内一直采用细网格)
        ratio: 在临界高度和半径之外，网格逐渐增大的比率.
    2024-02
    """
    vr = [0]
    while vr[-1] < radius:
        vr.append(vr[-1] + dr)
        if vr[-1] > rc:
            dr *= ratio
            if dr_max is not None:
                assert dr_max > 0
                dr = min(dr, dr_max)

    vx = [0]

    if height > 0:
        dh_backup = dh  # 备份，后续还需要
        while vx[-1] < height:
            vx.append(vx[-1] + dh)
            dh *= 1.5
        dh = dh_backup
        vx.reverse()
        vx = [-x for x in vx]  # 在海面以上部分的网格.

    while vx[-1] < depth:
        vx.append(vx[-1] + dh)
        if vx[-1] > hc:
            dh *= ratio
            if dh_max is not None:
                assert dh_max > 0
                dh = min(dh, dh_max)

    mesh = SeepageMesh.create_cylinder(x=vx, r=vr)

    for cell in mesh.cells:
        assert isinstance(cell, SeepageMesh.Cell)
        x, y, z = cell.pos
        cell.pos = [y, z, -x]

    return mesh
