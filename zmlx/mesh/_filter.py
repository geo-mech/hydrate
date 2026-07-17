"""
根据位置过滤 Mesh3，只保留指定范围内的 Node 及其关联的 Link、Face、Body。

作者: Claude Code
"""

from typing import Callable
from zmlx.exts import Mesh3


def filter_mesh(mesh: Mesh3, keep: Callable[[float, float, float], bool]) -> Mesh3:
    """
    创建一个新的 Mesh3，只保留 keep(x, y, z) 返回 True 的节点及其关联元素。

    过滤规则：如果某个 Node 不被保留，则所有引用它的 Link、Face、Body 均被丢弃。

    Args:
        mesh: 原始网格
        keep: 判定函数，接受 (x, y, z)，返回 True 表示保留该位置的 Node

    Returns:
        新的 Mesh3 对象
    """
    result = Mesh3()

    # --- 1. 过滤 Node ---
    node_keep = [False] * mesh.node_number
    node_map = {}
    for node in list(mesh.nodes):
        if keep(node.pos[0], node.pos[1], node.pos[2]):
            node_map[node.index] = result.node_number
            node_keep[node.index] = True
            result.add_node(node.pos[0], node.pos[1], node.pos[2])

    # --- 2. 过滤 Link ---
    # 先用 list() 收集，避免 result.add_node 干扰迭代器
    link_keep = [False] * mesh.link_number
    link_map = {}
    for link in list(mesh.links):
        nodes = list(link.nodes)
        if len(nodes) == 2 and node_keep[nodes[0].index] and node_keep[nodes[1].index]:
            n0 = node_map[nodes[0].index]
            n1 = node_map[nodes[1].index]
            link_map[link.index] = result.link_number
            link_keep[link.index] = True
            result.add_link([n0, n1])

    # --- 3. 过滤 Face ---
    face_keep = [False] * mesh.face_number
    face_map = {}
    for face in list(mesh.faces):
        links = list(face.links)
        if all(link_keep[lnk.index] for lnk in links):
            new_links = [link_map[lnk.index] for lnk in links]
            face_map[face.index] = result.face_number
            face_keep[face.index] = True
            result.add_face(new_links)

    # --- 4. 过滤 Body ---
    for body in list(mesh.bodies):
        faces = list(body.faces)
        if all(face_keep[fc.index] for fc in faces):
            new_faces = [face_map[fc.index] for fc in faces]
            result.add_body(new_faces)

    return result


def _check(name, mesh, exp_nodes, exp_bodies, exp_vol):
    """检查过滤结果的基本属性。"""
    ok = True
    if mesh.node_number != exp_nodes:
        print(f'  FAIL {name}: nodes={mesh.node_number} expect={exp_nodes}')
        ok = False
    if mesh.body_number != exp_bodies:
        print(f'  FAIL {name}: bodies={mesh.body_number} expect={exp_bodies}')
        ok = False
    total_vol = round(sum(b.volume for b in mesh.bodies), 10)
    if abs(total_vol - exp_vol) > 1e-10:
        print(f'  FAIL {name}: volume={total_vol} expect={exp_vol}')
        ok = False
    if ok:
        print(f'  OK   {name}: nodes={mesh.node_number} bodies={mesh.body_number} vol={total_vol}')


def test():
    """全面测试 filter_mesh。"""
    from zmlx.mesh._cube import create_cube_mesh

    mesh = create_cube_mesh(xs=[0, 1, 2], ys=[0, 2, 4], zs=[0, 3, 6])
    # 原始: 27 nodes, 54 links, 36 faces, 8 bodies, vol=48

    # --- 保留全部 ---
    f = filter_mesh(mesh, keep=lambda x, y, z: True)
    _check('全部保留', f, exp_nodes=27, exp_bodies=8, exp_vol=48)

    # --- 保留左半 (x≤1) ---
    f = filter_mesh(mesh, keep=lambda x, y, z: x <= 1)
    _check('x≤1', f, exp_nodes=18, exp_bodies=4, exp_vol=24)

    # --- 保留右半 (x≥1) ---
    f = filter_mesh(mesh, keep=lambda x, y, z: x >= 1)
    _check('x≥1', f, exp_nodes=18, exp_bodies=4, exp_vol=24)

    # --- 保留前半 (y≤2) ---
    f = filter_mesh(mesh, keep=lambda x, y, z: y <= 2)
    _check('y≤2', f, exp_nodes=18, exp_bodies=4, exp_vol=24)

    # --- 保留下半 (z≤3) ---
    f = filter_mesh(mesh, keep=lambda x, y, z: z <= 3)
    _check('z≤3', f, exp_nodes=18, exp_bodies=4, exp_vol=24)

    # --- 角落 (x≤1, y≤2, z≤3) ---
    f = filter_mesh(mesh, keep=lambda x, y, z: x <= 1 and y <= 2 and z <= 3)
    _check('角落', f, exp_nodes=8, exp_bodies=1, exp_vol=6)

    # --- 去掉全部 ---
    f = filter_mesh(mesh, keep=lambda x, y, z: False)
    _check('全部去掉', f, exp_nodes=0, exp_bodies=0, exp_vol=0)

    # --- 球心过滤 ---
    f = filter_mesh(mesh, keep=lambda x, y, z: (x - 1) ** 2 + (y - 2) ** 2 + (z - 3) ** 2 <= 1)
    print(f'  球心 (r≤1): nodes={f.node_number} bodies={f.body_number} vol={round(sum(b.volume for b in f.bodies), 4)}')

    # --- 单节点（只保留原点） ---
    f = filter_mesh(mesh, keep=lambda x, y, z: x == 0 and y == 0 and z == 0)
    _check('单节点', f, exp_nodes=1, exp_bodies=0, exp_vol=0)

    # --- 两节点一线（保留一条 Link 的两个端点） ---
    f = filter_mesh(mesh, keep=lambda x, y, z: (x == 0 or x == 1) and y == 0 and z == 0)
    _check('两点一线', f, exp_nodes=2, exp_bodies=0, exp_vol=0)

    # --- 10×8×5 网格 + 中间切片 ---
    big = create_cube_mesh(
        xs=[i * 0.1 for i in range(11)],
        ys=[j * 0.1 for j in range(9)],
        zs=[k * 0.1 for k in range(6)]
    )
    # 用整数索引避免浮点精度问题
    f = filter_mesh(big, keep=lambda x, y, z: 3 <= round(x * 10) <= 7 and 2 <= round(y * 10) <= 6)
    _check('10×8×5 切片', f, exp_nodes=5 * 5 * 6, exp_bodies=4 * 4 * 5, exp_vol=0.4 * 0.4 * 0.5)


if __name__ == '__main__':
    test()
