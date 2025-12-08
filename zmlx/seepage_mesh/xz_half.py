from zmlx.seepage_mesh.cube import create_cube


def create_xz_half(x_max=300.0, depth=300.0, height=100.0,
                   dx=2.0, dz=2.0,
                   hc=150, rc=100,
                   ratio=1.05,
                   dx_max=None, dz_max=None):
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
    if dx_max is None:
        dx_max = dx * 4.0
    vx = [0.0, dx]
    while vx[-1] < x_max:
        if vx[-1] > rc:  # 只有在超过这个区域之后，才可是尝试使用粗网格
            dx *= ratio
            dx = min(dx, dx_max)
        vx.append(vx[-1] + dx)
    # y方向在0附近，并且厚度等于1
    vy = [-0.5, 0.5]
    vz = [0.0]

    if height > 0:
        dz_backup = dz  # 备份，后续还需要
        while vz[-1] < height:
            vz.append(vz[-1] + dz)
            dz *= 1.5
        dz = dz_backup
        vz.reverse()
        vz = [-z for z in vz]  # 在海面以上部分的网格.

    if dz_max is None:
        dz_max = dz * 4.0
    while vz[-1] < depth:
        if vz[-1] > hc:  # 只有在超过这个范围之后，使用粗网格
            dz *= ratio
            dz = min(dz, dz_max)
        vz.append(vz[-1] + dz)

    #
    vz = [-z for z in vz]
    vz.reverse()

    return create_cube(x=vx, y=vy, z=vz)


if __name__ == '__main__':
    print(create_xz_half())
