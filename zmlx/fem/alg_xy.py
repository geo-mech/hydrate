"""
二维有限元相关的辅助算法。
"""

from zmlx.exts.base import DynSys, Mesh3


def add_node_fx(dyn: DynSys, node_id, fx):
    """
    添加一个节点力(x方向). 必须确保模型是二维的，并且在x-y平面。
    对于模型，自由度的顺序为：
        x0, y0, x1, y1, x2, y2 ...
    """
    p2f = dyn.get_p2f(node_id * 2)
    p2f.c += fx


def add_node_fy(dyn: DynSys, node_id, fy):
    """
    添加一个节点力(x方向). 必须确保模型是二维的，并且在x-y平面。
    对于模型，自由度的顺序为：
        x0, y0, x1, y1, x2, y2 ...
    """
    p2f = dyn.get_p2f(node_id * 2 + 1)
    p2f.c += fy


def add_node_force(dyn: DynSys, node_id, force):
    """
    添加一个节点力(x方向). 必须确保模型是二维的，并且在x-y平面。
    对于模型，自由度的顺序为：
        x0, y0, x1, y1, x2, y2 ...
    """
    assert len(force) == 2
    add_node_fx(dyn, node_id, force[0])
    add_node_fy(dyn, node_id, force[1])


def add_link_force(dyn: DynSys, mesh: Mesh3, link_id, force):
    """
    添加一个均布到一个link上的力. (将力平分到各个node)
    """
    assert link_id < mesh.link_number
    link = mesh.get_link(link_id)
    assert isinstance(link, Mesh3.Link)
    assert len(force) == 2
    force = [f / link.node_number for f in force]
    for node in link.nodes:
        assert isinstance(node, Mesh3.Node)
        add_node_force(dyn, node.index, force)


def add_face_pressure(dyn: DynSys, mesh: Mesh3, face_id, pressure, thick):
    """
    添加face内的流体压力。将这个压力，乘以这个face各个link的长度和thick，得到各个link上的力，并
    进而将这些力分配到各个node上。
    """
    if abs(pressure) < 1.0e-20:
        return

    assert face_id < mesh.face_number
    face = mesh.get_face(face_id)
    assert isinstance(face, Mesh3.Face)
    cent = face.pos

    for link in face.links:  # 遍历所有的边
        assert isinstance(link, Mesh3.Link)
        assert link.node_number == 2
        n0 = link.get_node(0)
        n1 = link.get_node(1)

        assert isinstance(n0, Mesh3.Node)
        assert isinstance(n1, Mesh3.Node)

        p0 = n0.pos
        p1 = n1.pos
        x0, y0 = p0[0], p0[1]
        x1, y1 = p1[0], p1[1]
        dx = x1 - x0
        dy = y1 - y0

        # link的长度
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length < 1.0e-20:
            continue

        # 计算垂直方向的向量
        perp = [-dy / length, dx / length]

        # 根据中心点，来确保方向朝外
        out_dir = (x0 - cent[0], y0 - cent[1])
        if out_dir[0] * perp[0] + out_dir[1] * perp[1] < 0:
            perp = [-item for item in perp]

        # 根据压力，计算作用在link上的向外的力
        force = [item * pressure * thick * length for item in perp]

        # 添加力
        add_link_force(dyn, mesh, link.index, force)
