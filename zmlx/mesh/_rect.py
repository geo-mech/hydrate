"""
在矩形区域内创建只有 Node、Link 和 Face（无 Body）的 Mesh3 网格。

作者: Claude Code
"""

from typing import Sequence
from zmlx.exts import Mesh3


def create_rect_mesh(
        xs: Sequence[float],
        ys: Sequence[float],
        z: float = 0.0
) -> Mesh3:
    """
    在 x-y 平面内创建矩形网格，包含 Node、Link 和 Face，不含 Body。

    Nodes: 位于所有 (x_i, y_j, z) 的网格点，共 nx × ny 个。
    Links: 连接相邻节点的水平边和垂直边。
    Faces: 每个矩形网格单元为一个四边形面，由 4 条 Link 围成。

    Args:
        xs: x 方向坐标（支持 list/tuple/numpy 等），长度 nx
        ys: y 方向坐标（支持 list/tuple/numpy 等），长度 ny
        z: 所有节点的 z 坐标（默认 0.0）

    Returns:
        包含 Node、Link、Face 的 Mesh3 对象
    """
    # 统一转为 Python float 列表（兼容 numpy 数组、元组等）
    xs = [float(x) for x in xs]
    ys = [float(y) for y in ys]

    nx, ny = len(xs), len(ys)
    if nx < 2 or ny < 2:
        raise ValueError(f'xs 和 ys 长度至少为 2，当前: nx={nx}, ny={ny}')

    def _is_monotonic(arr):
        return all(a < b for a, b in zip(arr, arr[1:])) or all(a > b for a, b in zip(arr, arr[1:]))

    if not _is_monotonic(xs):
        raise ValueError(f'xs 必须是单调的（升序或降序），当前: {xs}')
    if not _is_monotonic(ys):
        raise ValueError(f'ys 必须是单调的（升序或降序），当前: {ys}')

    mesh = Mesh3()

    # --- 1. 添加节点 ---
    # node_index(i, j) = j * nx + i
    for j in range(ny):
        for i in range(nx):
            mesh.add_node(xs[i], ys[j], z)

    def _node(i, j):
        return mesh.get_node(j * nx + i)

    # --- 2. 添加水平 Link（从左到右） ---
    h_links = {}  # (i, j) → Link index, 连接 (i,j) 和 (i+1,j)
    for j in range(ny):
        for i in range(nx - 1):
            n0 = _node(i, j)
            n1 = _node(i + 1, j)
            idx = mesh.add_link([n0.index, n1.index]).index
            h_links[(i, j)] = idx

    # --- 3. 添加垂直 Link（从下到上） ---
    v_links = {}  # (i, j) → Link index, 连接 (i,j) 和 (i,j+1)
    for j in range(ny - 1):
        for i in range(nx):
            n0 = _node(i, j)
            n1 = _node(i, j + 1)
            idx = mesh.add_link([n0.index, n1.index]).index
            v_links[(i, j)] = idx

    # --- 4. 添加 Face（每个矩形单元一个四边形面） ---
    # 四条边顺序: 左(bottom→top), 下(left→right), 右(bottom→top), 上(left→right)
    for j in range(ny - 1):
        for i in range(nx - 1):
            left = v_links[(i, j)]        # 左边: (i,j) → (i,j+1)
            bottom = h_links[(i, j)]       # 下边: (i,j) → (i+1,j)
            right = v_links[(i + 1, j)]    # 右边: (i+1,j) → (i+1,j+1)
            top = h_links[(i, j + 1)]      # 上边: (i,j+1) → (i+1,j+1)
            mesh.add_face([left, bottom, right, top])

    return mesh


def test():
    """测试：创建 101×51 的矩形网格并打印信息"""
    xs = [i * 0.1 for i in range(101)]  # 0 ~ 10, 步长 0.1
    ys = [j * 0.1 for j in range(51)]   # 0 ~ 5,  步长 0.1
    mesh = create_rect_mesh(xs=xs, ys=ys)

    print(f'Nodes: {mesh.node_number} (expect {len(xs) * len(ys)})')
    print(f'Links: {mesh.link_number} (expect {len(xs) * (len(ys) - 1) + (len(xs) - 1) * len(ys)})')
    print(f'Faces: {mesh.face_number} (expect {(len(xs) - 1) * (len(ys) - 1)})')
    print(f'Bodies: {mesh.body_number}')

    # 检查面积总和
    total_area = sum(face.area for face in mesh.faces)
    print(f'Total area: {total_area:.4f} (expect {10 * 5})')


if __name__ == '__main__':
    test()
