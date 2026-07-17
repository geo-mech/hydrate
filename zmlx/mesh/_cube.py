"""
在长方体区域内创建包含 Node、Link、Face 和 Body 的三维 Mesh3 网格。

作者: Claude Code
"""

from typing import Sequence
from zmlx.exts import Mesh3


def create_cube_mesh(
        xs: Sequence[float],
        ys: Sequence[float],
        zs: Sequence[float]
) -> Mesh3:
    """
    在三维空间内创建长方体网格，包含 Node、Link 和 Face，不含 Body。

    Nodes: 位于所有 (x_i, y_j, z_k) 的网格点，共 nx × ny × nz 个。
    Links: 连接相邻节点的 x/y/z 三个方向的边。
    Faces: 每个长方体单元有 6 个四边形面，由 4 条 Link 围成。

    Args:
        xs: x 方向坐标（支持 list/tuple/numpy 等），长度 nx
        ys: y 方向坐标（支持 list/tuple/numpy 等），长度 ny
        zs: z 方向坐标（支持 list/tuple/numpy 等），长度 nz

    Returns:
        包含 Node、Link、Face 的 Mesh3 对象
    """
    # 统一转为 Python float 列表（兼容 numpy 数组、元组等）
    xs = [float(x) for x in xs]
    ys = [float(y) for y in ys]
    zs = [float(z) for z in zs]

    nx, ny, nz = len(xs), len(ys), len(zs)
    if nx < 2 or ny < 2 or nz < 2:
        raise ValueError(f'xs, ys, zs 长度至少为 2，当前: nx={nx}, ny={ny}, nz={nz}')

    def _is_monotonic(arr):
        return all(a < b for a, b in zip(arr, arr[1:])) or all(a > b for a, b in zip(arr, arr[1:]))

    if not _is_monotonic(xs):
        raise ValueError(f'xs 必须是单调的（升序或降序），当前: {xs}')
    if not _is_monotonic(ys):
        raise ValueError(f'ys 必须是单调的（升序或降序），当前: {ys}')
    if not _is_monotonic(zs):
        raise ValueError(f'zs 必须是单调的（升序或降序），当前: {zs}')

    mesh = Mesh3()

    # --- 1. 添加节点 ---
    # node_index(i, j, k) = (k * ny + j) * nx + i
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                mesh.add_node(xs[i], ys[j], zs[k])

    def _node(i, j, k):
        return mesh.get_node((k * ny + j) * nx + i)

    # --- 2. 添加 x 方向 Link ---
    # (i,j,k) → (i+1,j,k)
    hx = {}  # (i, j, k) → Link index
    for k in range(nz):
        for j in range(ny):
            for i in range(nx - 1):
                n0 = _node(i, j, k)
                n1 = _node(i + 1, j, k)
                hx[(i, j, k)] = mesh.add_link([n0.index, n1.index]).index

    # --- 3. 添加 y 方向 Link ---
    # (i,j,k) → (i,j+1,k)
    hy = {}  # (i, j, k) → Link index
    for k in range(nz):
        for j in range(ny - 1):
            for i in range(nx):
                n0 = _node(i, j, k)
                n1 = _node(i, j + 1, k)
                hy[(i, j, k)] = mesh.add_link([n0.index, n1.index]).index

    # --- 4. 添加 z 方向 Link ---
    # (i,j,k) → (i,j,k+1)
    hz = {}  # (i, j, k) → Link index
    for k in range(nz - 1):
        for j in range(ny):
            for i in range(nx):
                n0 = _node(i, j, k)
                n1 = _node(i, j, k + 1)
                hz[(i, j, k)] = mesh.add_link([n0.index, n1.index]).index

    # --- 5. 添加 Face（每个长方体单元 6 个面） ---
    # 记录每个单元格的 6 个面索引，用于后续创建 Body
    cell_faces = [[None] * 6 for _ in range((nx - 1) * (ny - 1) * (nz - 1))]

    def _cell_idx(i, j, k):
        return (k * (ny - 1) + j) * (nx - 1) + i

    for k in range(nz - 1):
        for j in range(ny - 1):
            for i in range(nx - 1):
                ci = _cell_idx(i, j, k)
                # Bottom (z-plane at k)
                cell_faces[ci][0] = mesh.add_face([
                    hy[(i, j, k)], hx[(i, j, k)],
                    hy[(i + 1, j, k)], hx[(i, j + 1, k)],
                ]).index
                # Top (z-plane at k+1)
                cell_faces[ci][1] = mesh.add_face([
                    hy[(i, j, k + 1)], hx[(i, j, k + 1)],
                    hy[(i + 1, j, k + 1)], hx[(i, j + 1, k + 1)],
                ]).index
                # Front (y-plane at j)
                cell_faces[ci][2] = mesh.add_face([
                    hz[(i, j, k)], hx[(i, j, k)],
                    hz[(i + 1, j, k)], hx[(i, j, k + 1)],
                ]).index
                # Back (y-plane at j+1)
                cell_faces[ci][3] = mesh.add_face([
                    hz[(i, j + 1, k)], hx[(i, j + 1, k)],
                    hz[(i + 1, j + 1, k)], hx[(i, j + 1, k + 1)],
                ]).index
                # Left (x-plane at i)
                cell_faces[ci][4] = mesh.add_face([
                    hz[(i, j, k)], hy[(i, j, k)],
                    hz[(i, j + 1, k)], hy[(i, j, k + 1)],
                ]).index
                # Right (x-plane at i+1)
                cell_faces[ci][5] = mesh.add_face([
                    hz[(i + 1, j, k)], hy[(i + 1, j, k)],
                    hz[(i + 1, j + 1, k)], hy[(i + 1, j, k + 1)],
                ]).index

    # --- 6. 添加 Body（每个长方体单元一个体） ---
    for faces in cell_faces:
        mesh.add_body(faces)

    return mesh


def _check(name, mesh, exp_nodes, exp_bodies, exp_vol):
    """检查网格的基本属性是否与预期一致。"""
    ok = True
    if mesh.node_number != exp_nodes:
        print(f'  FAIL {name}: nodes={mesh.node_number} expect={exp_nodes}')
        ok = False
    if mesh.body_number != exp_bodies:
        print(f'  FAIL {name}: bodies={mesh.body_number} expect={exp_bodies}')
        ok = False
    total_vol = sum(b.volume for b in mesh.bodies)
    total_vol = round(total_vol, 10)  # 消除浮点累积误差
    if abs(total_vol - exp_vol) > 1e-10:
        print(f'  FAIL {name}: volume={total_vol} expect={exp_vol}')
        ok = False
    if ok:
        print(f'  OK   {name}: nodes={mesh.node_number} bodies={mesh.body_number} vol={total_vol}')


def test():
    """全面测试 create_cube_mesh。"""

    # --- 单立方体 ---
    m = create_cube_mesh(xs=[0, 1], ys=[0, 2], zs=[0, 3])
    _check('单立方体', m, exp_nodes=8, exp_bodies=1, exp_vol=6)

    # --- 两个相邻（x 方向） ---
    m = create_cube_mesh(xs=[0, 1, 2], ys=[0, 2], zs=[0, 3])
    _check('x 方向 ×2', m, exp_nodes=12, exp_bodies=2, exp_vol=12)

    # --- 两个相邻（y 方向） ---
    m = create_cube_mesh(xs=[0, 1], ys=[0, 2, 4], zs=[0, 3])
    _check('y 方向 ×2', m, exp_nodes=12, exp_bodies=2, exp_vol=12)

    # --- 两个相邻（z 方向） ---
    m = create_cube_mesh(xs=[0, 1], ys=[0, 2], zs=[0, 3, 6])
    _check('z 方向 ×2', m, exp_nodes=12, exp_bodies=2, exp_vol=12)

    # --- 2×2×2 网格 ---
    m = create_cube_mesh(xs=[0, 1, 2], ys=[0, 2, 4], zs=[0, 3, 6])
    _check('2×2×2', m, exp_nodes=27, exp_bodies=8, exp_vol=48)

    # --- 降序 ---
    m = create_cube_mesh(xs=[2, 0], ys=[4, 0], zs=[6, 0])
    _check('降序', m, exp_nodes=8, exp_bodies=1, exp_vol=2 * 4 * 6)

    # --- 非均匀间距 ---
    m = create_cube_mesh(xs=[0, 0.5, 2], ys=[0, 3], zs=[0, 1])
    _check('非均匀', m, exp_nodes=12, exp_bodies=2, exp_vol=6)

    # --- 中等网格 10×8×5 ---
    m = create_cube_mesh(
        xs=[i * 0.1 for i in range(11)],
        ys=[j * 0.1 for j in range(9)],
        zs=[k * 0.1 for k in range(6)]
    )
    _check('10×8×5', m, exp_nodes=11 * 9 * 6, exp_bodies=10 * 8 * 5,
           exp_vol=1.0 * 0.8 * 0.5)

    # --- numpy 输入 ---
    try:
        import numpy as np
        m = create_cube_mesh(
            xs=np.linspace(0, 1, 5),
            ys=np.linspace(0, 2, 3),
            zs=np.array([0, 3])
        )
        _check('numpy', m, exp_nodes=5 * 3 * 2, exp_bodies=4 * 2 * 1, exp_vol=6)
    except ImportError:
        print('  SKIP numpy (not installed)')

    # --- 非法输入 ---
    for name, args in [
        ('长度不足', dict(xs=[0], ys=[0, 1], zs=[0, 1])),
        ('xs 非单调', dict(xs=[0, 2, 1], ys=[0, 1], zs=[0, 1])),
        ('ys 非单调', dict(xs=[0, 1], ys=[0, 2, 1], zs=[0, 1])),
        ('zs 非单调', dict(xs=[0, 1], ys=[0, 1], zs=[0, 2, 1])),
    ]:
        try:
            create_cube_mesh(**args)
            print(f'  FAIL {name}: 应抛出异常')
        except ValueError:
            print(f'  OK   {name}: 正确拦截')


if __name__ == '__main__':
    test()
