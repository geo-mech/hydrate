from zml import *


def update_seepage_topology(seepage, fixed_n, layer_n, network, fa_id, fa_new, z_range, cell_new=None, face_new=None):
    """
    根据二维裂缝网络的结构，来更新seepage的结构。

    假设seepage中的单元分为两类，分别为固定单元（代表天然裂缝）和活动单元（主裂缝）。
    在seepage中，共有fixed_n个固定单元。这些固定单元在前面，活动单元在后面.

    活动的单元又分为layer_n层，且每层的单元的数量和网络的结构是完全相同的.

    在network的每一个裂缝中，都存储一个属性fa_id，表示这个单元对应的seepage每一层的
    cell的id.

    计算主要分为3步：
        1、将最后的layer_n层Cell弹出来;
        2、利用network的结构来更新这些层；
        3、将更新了结构的Cell和Face再重新压入到seepage中，并且建立这些层之间的连接(Face)

    返回：
        新的裂缝单元的数量.
    """
    assert isinstance(seepage, Seepage)
    assert isinstance(network, FractureNetwork2)
    assert fixed_n <= seepage.cell_number
    assert layer_n >= 1
    assert fa_id is not None
    assert fa_new is not None

    active_n = seepage.cell_number - fixed_n
    assert active_n % layer_n == 0
    layer_cell_n = active_n // layer_n
    assert isinstance(layer_cell_n, int)  # 必须确保是int，否则后面传入dll的时候会出错
    assert layer_cell_n * layer_n + fixed_n == seepage.cell_number

    # 将最后的layer_n层Cell弹出来
    timer.beg('update_seepage_topology.pop_cells')
    layers = []
    ibeg = fixed_n
    for layer_i in range(layer_n):
        lay = Seepage()
        while lay.cell_number < layer_cell_n:
            lay.add_cell()
        assert lay.cell_number == layer_cell_n
        kwargs = create_dict(ibeg0=0, other=seepage, ibeg1=ibeg, count=layer_cell_n)
        lay.clone_cells(**kwargs)
        lay.clone_inner_faces(**kwargs)
        layers.append(lay)
        ibeg += layer_cell_n
    seepage.pop_cells(active_n)
    assert seepage.cell_number == fixed_n
    timer.end('update_seepage_topology.pop_cells')

    # 利用network的结构来更新这些层
    timer.beg('update_seepage_topology.update_layers')
    fractures = network.get_fractures()
    cell_ids = []  # 备份fa_id
    for frac in fractures:
        cell_ids.append(frac.get_attr(fa_id))
    for layer_i in range(layer_n):
        if layer_i > 0:  # 恢复备份的fa_id (第一层不需要)
            for i in range(len(fractures)):
                frac = fractures[i]
                frac.set_attr(fa_id, cell_ids[i])
        lay = layers[layer_i]
        Hf2Alg.update_seepage_topology(seepage=lay, network=network, fa_id=fa_id,
                                       fa_new=fa_new, cell_new=cell_new, face_new=face_new
                                       )
    timer.end('update_seepage_topology.update_layers')

    # 更新各个Cell的位置
    timer.beg('update_seepage_topology.update_cells')
    z_min, z_max = (-1, 1) if z_range is None else z_range
    layer_h = (z_max - z_min) / layer_n
    layer_z = [z_min + layer_h * (layer_i + 0.5) for layer_i in range(layer_n)]
    new_n = 0  # 新的裂缝单元的数量
    for frac in network.get_fractures():
        is_new = frac.get_attr(fa_new)
        if abs(is_new - 1) > 0.1:  # 对于新的裂缝，is_new的数值等于1
            continue
        new_n += 1
        x0, y0, x1, y1 = frac.pos
        x = (x0 + x1) / 2
        y = (y0 + y1) / 2
        cell_id = round(frac.get_attr(fa_id))
        for layer_i in range(layer_n):
            lay = layers[layer_i]
            assert 0 <= cell_id < lay.cell_number
            cell = lay.get_cell(cell_id)
            cell.pos = (x, y, layer_z[layer_i])
    timer.end('update_seepage_topology.update_cells')

    # 将更新了结构的Cell和Face再重新压入到seepage中，并且建立这些层之间的连接(Face)
    timer.beg('update_seepage_topology.push_cells')
    for layer_i in range(layer_n):
        lay = layers[layer_i]
        if layer_i == 0:  # 仅仅追加，不创建Face
            seepage.append(lay, cell_i0=None)
        else:  # 追加，并且添加和前面一层的Face
            cell_i0 = seepage.cell_number - lay.cell_number
            assert cell_i0 >= 0
            seepage.append(lay, cell_i0=cell_i0)
    timer.end('update_seepage_topology.push_cells')

    return new_n


def test():
    """
    测试
    """
    seepage, network = Seepage(), FractureNetwork2()
    for i in range(5):
        network.add_fracture(pos=[i * 2, 0, i * 2 + 1, 0], lave=0.1)
        update_seepage_topology(seepage, fixed_n=0, layer_n=5, network=network, fa_id=0, fa_new=1,
                                z_range=[-10, 10], cell_new=0, face_new=0)
        print(network.frac_n)
        print(seepage)


if __name__ == '__main__':
    test()
