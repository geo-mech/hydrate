from zml import FractureNetwork, Seepage


def set_seepage_topology(model: Seepage, network: FractureNetwork):
    """更新渗流模型的结构(针对单层的模型)。

    会清除现有cell和face后重新构建网络结构，模型参数将被重置为默认值。

    Args:
        model (Seepage): 需要更新的渗流模型
        network (FractureNetwork): 裂缝网络对象

    Returns:
        None
    """
    # 首先，清除模型中现有的所有的单元和面
    model.clear_cells_and_faces()

    # 添加单元
    while model.cell_number < network.fracture_number:
        model.add_cell()

    # 添加Face
    count = 0
    for vertex in network.vertexes:
        assert isinstance(vertex, FractureNetwork.Vertex)
        frac_n = vertex.fracture_number
        for i0 in range(frac_n):
            i0x = vertex.get_fracture(i0).index
            for i1 in range(i0 + 1, frac_n):
                i1x = vertex.get_fracture(i1).index
                assert i0x != i1x
                assert i0x < model.cell_number and i1x < model.cell_number
                model.add_face(i0x, i1x)
                count += 1
    if count != model.face_number:
        print(
            f'meet error when add faces. count = {count}, '
            f'face_number = {model.face_number}')
