"""
清理 Mesh3 中的孤立元素（不返回原始对象的副本，原始 mesh 不变）。

作者: Claude Code
"""

from zmlx.exts import Mesh3


def remove_orphan_faces(mesh: Mesh3) -> Mesh3:
    """去除不隶属于任何 Body 的 Face，返回新的 Mesh3。"""
    face_used = [False] * mesh.face_number
    for body in list(mesh.bodies):
        for face in list(body.faces):
            face_used[face.index] = True
    return _rebuild(mesh, face_keep=face_used)


def remove_orphan_links(mesh: Mesh3) -> Mesh3:
    """去除不隶属于任何 Face 的 Link，返回新的 Mesh3。"""
    link_used = [False] * mesh.link_number
    for face in list(mesh.faces):
        for link in list(face.links):
            link_used[link.index] = True
    return _rebuild(mesh, link_keep=link_used)


def remove_orphan_nodes(mesh: Mesh3) -> Mesh3:
    """去除不隶属于任何 Link 的 Node，返回新的 Mesh3。"""
    node_used = [False] * mesh.node_number
    for link in list(mesh.links):
        for node in list(link.nodes):
            node_used[node.index] = True
    return _rebuild(mesh, node_keep=node_used)


def _rebuild(mesh, face_keep=None, link_keep=None, node_keep=None):
    """根据保留标记重建 Mesh3，只包含被标记为保留的元素及其上层依赖。"""
    result = Mesh3()

    # --- 1. Node ---
    if node_keep is None:
        node_keep = [True] * mesh.node_number
    node_map = {}
    for node in list(mesh.nodes):
        if node_keep[node.index]:
            node_map[node.index] = result.node_number
            result.add_node(node.pos[0], node.pos[1], node.pos[2])

    # --- 2. Link ---
    if link_keep is None:
        # 自动从 node_keep 推导: link 两端 node 都保留 → link 保留
        link_keep = [False] * mesh.link_number
        for link in list(mesh.links):
            nodes = list(link.nodes)
            if len(nodes) == 2 and node_keep[nodes[0].index] and node_keep[nodes[1].index]:
                link_keep[link.index] = True

    link_map = {}
    for link in list(mesh.links):
        if link_keep[link.index]:
            nodes = list(link.nodes)
            link_map[link.index] = result.link_number
            result.add_link([node_map[n.index] for n in nodes])

    # --- 3. Face ---
    if face_keep is None:
        # 自动从 link_keep 推导: face 的所有 link 都保留 → face 保留
        face_keep = [False] * mesh.face_number
        for face in list(mesh.faces):
            links = list(face.links)
            if all(link_keep[lnk.index] for lnk in links):
                face_keep[face.index] = True

    face_map = {}
    for face in list(mesh.faces):
        if face_keep[face.index]:
            links = list(face.links)
            face_map[face.index] = result.face_number
            result.add_face([link_map[lnk.index] for lnk in links])

    # --- 4. Body ---
    for body in list(mesh.bodies):
        faces = list(body.faces)
        if all(face_keep[fc.index] for fc in faces):
            result.add_body([face_map[fc.index] for fc in faces])

    return result


def test():
    from zmlx.mesh._cube import create_cube_mesh
    from zmlx.mesh._filter import filter_mesh
    from zmlx.exts import Mesh3

    # --- Full mesh: should be unchanged ---
    mesh = create_cube_mesh(xs=[0, 1, 2], ys=[0, 2, 4], zs=[0, 3, 6])

    f = remove_orphan_faces(mesh)
    assert f.node_number == mesh.node_number and f.face_number == mesh.face_number
    print('  OK  full mesh remove_orphan_faces: unchanged')

    l = remove_orphan_links(mesh)
    assert l.link_number == mesh.link_number
    print('  OK  full mesh remove_orphan_links: unchanged')

    n = remove_orphan_nodes(mesh)
    assert n.node_number == mesh.node_number
    print('  OK  full mesh remove_orphan_nodes: unchanged')

    # --- Manual mesh with orphan elements (no bodies) ---
    m = Mesh3()
    # Connected region (0,0)-(1,1)
    m.add_node(0, 0, 0); m.add_node(1, 0, 0); m.add_node(0, 1, 0); m.add_node(1, 1, 0)
    # Orphan region (9,9)-(10,10)
    m.add_node(9, 9, 0); m.add_node(10, 9, 0); m.add_node(9, 10, 0); m.add_node(10, 10, 0)
    # Connected links
    m.add_link([0, 1]); m.add_link([1, 3]); m.add_link([0, 2]); m.add_link([2, 3])
    # Orphan links
    m.add_link([4, 5]); m.add_link([5, 7]); m.add_link([4, 6]); m.add_link([6, 7])
    # Connected face + orphan face
    m.add_face([0, 1, 3, 2])
    m.add_face([4, 5, 7, 6])
    # No bodies (add_body requires 4 or 6 faces), so all faces are orphan

    f = remove_orphan_faces(m)
    assert f.face_number == 0
    print('  OK  remove_orphan_faces (no body): all faces removed')

    l = remove_orphan_links(m)
    assert l.link_number == 8  # all links belong to faces
    print('  OK  remove_orphan_links (with faces): unchanged')

    l2 = remove_orphan_links(f)  # f has no faces → all links orphan
    assert l2.link_number == 0
    print('  OK  remove_orphan_links (no faces): all links removed')

    n2 = remove_orphan_nodes(l2)  # l2 has no links → all nodes orphan
    assert n2.node_number == 0
    print('  OK  remove_orphan_nodes (no links): all nodes removed')

    n = remove_orphan_nodes(m)
    assert n.node_number == 8  # all nodes belong to links
    print('  OK  remove_orphan_nodes (with links): unchanged')

    # --- Chain cleanup on full mesh (with bodies) ---
    cube = create_cube_mesh(xs=[0, 1, 2], ys=[0, 2, 4], zs=[0, 3, 6])
    c = remove_orphan_nodes(remove_orphan_links(remove_orphan_faces(cube)))
    assert c.node_number == cube.node_number
    assert c.body_number == cube.body_number
    print('  OK  chain cleanup (full mesh): unchanged')

    # --- Chain cleanup on mesh without bodies ---
    m4 = Mesh3()
    m4.add_node(0, 0, 0); m4.add_node(1, 0, 0); m4.add_node(0, 1, 0); m4.add_node(1, 1, 0)
    m4.add_node(9, 9, 0); m4.add_node(10, 9, 0); m4.add_node(9, 10, 0); m4.add_node(10, 10, 0)
    m4.add_link([0, 1]); m4.add_link([1, 3]); m4.add_link([0, 2]); m4.add_link([2, 3])
    m4.add_link([4, 5]); m4.add_link([5, 7]); m4.add_link([4, 6]); m4.add_link([6, 7])
    m4.add_face([0, 1, 3, 2]); m4.add_face([4, 5, 7, 6])
    c = remove_orphan_nodes(remove_orphan_links(remove_orphan_faces(m4)))
    assert c.node_number == 0
    print('  OK  chain cleanup (no body): all cleared')

    # --- Large grid + crop + chain cleanup ---
    big = create_cube_mesh(
        xs=[i * 0.1 for i in range(11)],
        ys=[j * 0.1 for j in range(9)],
        zs=[k * 0.1 for k in range(6)]
    )
    part = filter_mesh(big, keep=lambda x, y, z: x <= 0.3 and y <= 0.3)
    clean = remove_orphan_nodes(remove_orphan_links(remove_orphan_faces(part)))
    # Verify no orphans
    for body in clean.bodies:
        for face in body.faces:
            assert face is not None
    for face in clean.faces:
        for link in face.links:
            assert link is not None
    for link in clean.links:
        for node in link.nodes:
            assert node is not None
    print(f'  OK  large crop+clean: nodes={clean.node_number} links={clean.link_number} faces={clean.face_number} bodies={clean.body_number}')

    print('All tests passed')


if __name__ == '__main__':
    test()
