from zml import Mesh3


def cube2tet(body: Mesh3.Body, to_local=False):
    """
    将1个六面体分成5个4面体. 其中的body为Mesh3的一个体(Mesh3.Body). 返回5个list，其中每个list包含
    4个元素，分别为四面体4个顶点对应的node的ID。如果to_local，则返回Body中的node的ID，否则，返回
    全局的ID.

    剖分方法参考：
        https://forum.taichi-lang.cn/t/topic/4378
    """
    assert body.node_number == 8
    assert body.link_number == 12
    assert body.face_number == 6

    # 尚未组成四面体的link
    link_ids = set([link.index for link in body.links])

    # 尚未用于四面体的node
    node_ids = []

    tets = []  # 所有的四面体
    for node in body.nodes:
        assert isinstance(node, Mesh3.Node)
        links = [link for link in node.links if link.index in link_ids]
        assert len(links) <= 3
        if len(links) == 3:  # 组成一个四面体
            tet = set()
            for link in links:
                link_ids.remove(link.index)
                for n in link.nodes:
                    tet.add(n.index)
            assert len(tet) == 4
            tets.append(list(tet))
        else:
            node_ids.append(node.index)
    assert len(tets) == 4
    assert len(node_ids) == 4
    tets.append(node_ids)

    if to_local:  # 将全局的ID转化为局部的ID.
        idx_map = {}
        for i0 in range(body.node_number):
            i1 = body.get_node(i0).index
            idx_map[i1] = i0
        for tet in tets:
            for i in range(len(tet)):
                tet[i] = idx_map[tet[i]]

    # 返回所有的四面体.
    return tets


if __name__ == '__main__':
    mesh = Mesh3.create_cube(x1=0, y1=0, z1=0, x2=2, y2=1, z2=1, dx=1, dy=1,
                             dz=1)
    print(mesh)
    tets = cube2tet(mesh.get_body(1), to_local=True)
    print(tets)
