"""
评估裂缝网络的拓扑结构
"""
from typing import List, Set, Optional, Iterable, Tuple

from zmlx.exts import FractureNetwork

INT_MAX = 99999999999


def fill_vertexes(
        network: FractureNetwork, vertex_start: Optional[int] = None
) -> Optional[Set[int]]:
    """
    基于一个裂缝网络，给定一个顶点作为起点，通过填充连通的Vertex (floodfill)，获取所有被填充的Vertex的集合. 此函数的目的，是首先
    从一个很大的网络中，抽离出那些和起点相关的(连通的)部分用于后续的操作.
    Args:
        network: 裂缝网络对象
        vertex_start: 搜索起点的Vertex的索引
    Returns:
        被填充的Vertex的集合
    """
    # 检查start是否有效
    vertex = network.get_vertex(vertex_start)
    if vertex is None:
        return set(range(network.vertex_number))  # 此时，返回所有顶点的集合

    # 标记过的顶点.
    vertex_ids_marked: Set[int] = {vertex.index}
    vertexes: List[FractureNetwork.Vertex] = [vertex]

    for i in range(INT_MAX):
        if i >= len(vertexes):
            break

        vertex = vertexes[i]
        for next_vertex in vertex.vertexes:
            if next_vertex.index not in vertex_ids_marked:
                vertex_ids_marked.add(next_vertex.index)
                vertexes.append(next_vertex)

    # 返回被填充过的顶点序号的集合
    return vertex_ids_marked


def test_1():
    """
    测试fill_vertexes函数
    """
    network = FractureNetwork()
    print(fill_vertexes(network, 0))

    network.add_fracture(first=[0, 0], second=[0, 1], lave=0.1)
    print(network)
    print(fill_vertexes(network, 0))
    print(fill_vertexes(network))

    network.add_fracture(first=[1, 0], second=[1, 1], lave=0.1)
    print(network)
    print(fill_vertexes(network, 0))
    print(fill_vertexes(network, -1))

    network.add_fracture(first=[-0.2, 0.5], second=[1.2, 0.5], lave=0.1)
    print(network)
    print(fill_vertexes(network, -1))
    print(fill_vertexes(network))


# if __name__ == '__main__':
#     test_1()


def fill_inner_fractures(
        network: FractureNetwork,
        fracture_start: int,
        special_vertexes: Optional[Iterable[int]] = None
) -> Tuple[Optional[List[int]], Optional[Set[int]]]:
    """
    给定一个裂缝，从这个裂缝开始填充，遇到特殊的顶点就停止，返回填充的裂缝和特殊的顶点.
    Args:
        network: 裂缝网络对象
        fracture_start: 起点的裂缝单元的索引
        special_vertexes: 特殊的顶点集合(除此之外，所有裂缝数量不等于2的顶点也被视为特殊的顶点). 这些特殊的顶点不会被消除.
    Returns:
        tips: 特殊的顶点序号列表
        fracture_ids_marked: 被填充的裂缝序号集合
    """
    fracture = network.get_fracture(fracture_start)
    if fracture is None:
        return None, None

    fracture_ids_marked: Set[int] = {fracture.index}
    fractures: List[FractureNetwork.Fracture] = [fracture]
    tips: List[int] = []

    special_copy = set()
    if special_vertexes is not None:
        for idx in special_vertexes:
            vertex = network.get_vertex(idx)
            if vertex is not None:
                special_copy.add(vertex.index)

    def is_special(idx_):
        """
        判断给定序号的顶点是否是特殊顶点
        """
        if idx_ in special_copy:
            return True
        vtx = network.get_vertex(idx_)
        assert vtx is not None
        return vtx.fracture_number != 2

    for i in range(INT_MAX):
        if i >= len(fractures):
            break

        fracture = fractures[i]
        for vertex in fracture.vertexes:
            if is_special(vertex.index):
                tips.append(vertex.index)
            else:
                assert vertex.fracture_number == 2
                f0 = vertex.get_fracture(0)
                f1 = vertex.get_fracture(1)
                assert f0 is not None and f1 is not None
                if fracture.index == f0.index:
                    another = f1
                else:
                    assert fracture.index == f1.index
                    another = f0
                if another.index not in fracture_ids_marked:
                    fracture_ids_marked.add(another.index)
                    fractures.append(another)

    assert len(tips) == 2, f'A fracture string must have two vertex. len(tips) = {len(tips)}'
    return tips, fracture_ids_marked


def test_2():
    """
    测试fill_inner_fractures函数
    """
    network = FractureNetwork()
    network.add_fracture(first=[0, -1], second=[0, 1], lave=0.2)
    network.add_fracture(first=[-1, 0], second=[1, 0], lave=0.2)
    print(network)
    print(fill_inner_fractures(network, -1))


# if __name__ == '__main__':
#     test_2()


def get_topo(
        network: FractureNetwork, vertex_start: Optional[int] = None
) -> Tuple[Optional[List[List[int]]], Optional[List[List[int]]]]:
    """
    返回以给定的顶点开始，所联系的网络的结构. 所谓的结构，就是将相关的裂缝网络，用“一串串”的裂缝单元来表述.
    Returns:
        v_tips: 裂缝链条两侧的特殊顶点序号列表
        v_fids: 裂缝链条列表
    """
    vertexes = fill_vertexes(network, vertex_start)  # 所有相关的顶点的序号
    if vertexes is None:
        return None, None

    fracture_ids: Set[int] = set()  # 所有相关的裂缝单元

    for idx in vertexes:
        vertex = network.get_vertex(idx)
        assert vertex is not None
        for f in vertex.fractures:
            fracture_ids.add(f.index)

    v_tips: List[List[int]] = []  # 裂缝链条两侧的特殊顶点序号
    v_fids: List[List[int]] = []  # 裂缝链条

    special_vertexes: List[int] = []
    if vertex_start is not None:
        special_vertexes.append(vertex_start)

    while len(fracture_ids) > 0:
        fracture_id = fracture_ids.pop()  # 抽取一个裂缝以开始
        tips, fracture_ids_marked = fill_inner_fractures(network, fracture_id, special_vertexes=special_vertexes)

        assert tips is not None
        assert len(tips) == 2
        assert fracture_ids_marked is not None

        for fid in fracture_ids_marked:
            if fid in fracture_ids:
                fracture_ids.remove(fid)

        v_tips.append(tips)
        v_fids.append(list(fracture_ids_marked))

    return v_tips, v_fids


def test_3():
    """
    测试get_topo函数
    """
    network = FractureNetwork()
    network.add_fracture(first=[0, -1], second=[0, 1], lave=0.2)
    network.add_fracture(first=[-1, 0], second=[1, 0], lave=0.2)
    network.add_fracture(first=[-1, 4], second=[1, 4], lave=0.2)
    print(network)
    v_tips, v_fids = get_topo(network)
    print(v_tips)
    print(v_fids)


if __name__ == '__main__':
    test_3()
