from zml import Seepage, FractureNetwork2, Hf2Alg, Fracture2
from zmlx.alpha.hf2 import CellKeys, FracKeys, FaceKeys
from zmlx.alpha.hf2 import dfn_v3


def push_layers(seepage, layers):
    """
    将多层的渗流模型追加到 seepage中，并在各个层之间建立连接.

    注意:
        在此函数运行之后，layers的数据仍然需要保留. 因为后续在pop这些layers数据的时候，
        需要用到现有的结构.
    """
    if len(layers) == 0:
        return

    layer_cell_n = layers[0].cell_number
    for lay in layers:
        assert lay.cell_number == layer_cell_n

    assert isinstance(seepage, Seepage)
    cell_n = seepage.cell_number

    for lay in layers:
        assert isinstance(lay, Seepage)
        face_n = seepage.face_number
        seepage.append(lay, None if seepage.cell_number == cell_n else seepage.cell_number - layer_cell_n)

        # 下面，设置Face的tag，用以区分不同的Face的种类.
        assert seepage.face_number - face_n >= lay.face_number
        for idx in range(face_n, face_n+lay.face_number):
            face = seepage.get_face(idx)
            face.set_attr(FaceKeys.tag, 1)
        for idx in range(face_n+lay.face_number, seepage.face_number):
            face = seepage.get_face(idx)
            face.set_attr(FaceKeys.tag, 2)


def get_cell_ibeg(layers, seepage, layer_id):
    """
    返回第layer_id层的第一个Cell在seepage的ID
    """
    i_beg1 = seepage.cell_number
    for lay in layers:
        i_beg1 -= lay.cell_number
    assert i_beg1 >= 0
    for i in range(layer_id):
        i_beg1 += layers[i].cell_number
    return i_beg1


def pop_layers(layers, seepage):
    """
    将seepage中的cell数据，复制到对应的layers的cell中，然后在seepage中，移除这些层对应的这些cell.
    此函数不会修改layers的结构.
    要求:
        这些层所对应的这些cell，应该在这个seepage模型的最后面
    """
    assert isinstance(seepage, Seepage)

    i_beg1 = seepage.cell_number
    for lay in layers:
        i_beg1 -= lay.cell_number
    assert i_beg1 >= 0

    for lay in layers:
        lay.clone_cells(0, seepage, i_beg1, lay.cell_number)
        i_beg1 += lay.cell_number

    for lay in layers:
        seepage.pop_cells(lay.cell_number)


def update_layers_topology(layers, network, layer_h, z_average=0):
    """
    更新各个层的结构。必须确保，这些层的结构仅仅被这个函数所管理，即，在这个函数之外
    任何地方都不要修改这些layers的结构.
    """
    assert isinstance(network, FractureNetwork2)
    network.copy_attr(FracKeys.tmp, FracKeys.id)
    layer_n = len(layers)
    assert layer_n >= 1
    for layer_id in range(layer_n):
        lay = layers[layer_id]
        network.copy_attr(FracKeys.id, FracKeys.tmp)
        Hf2Alg.update_seepage_topology(seepage=lay, network=network, fa_id=FracKeys.id)
        # todo: 下面，逐个单元设置，可能效率比较低
        z0 = (layer_id - layer_n / 2) * layer_h + z_average
        z1 = z0 + layer_h
        for fr in network.get_fractures():
            assert isinstance(fr, Fracture2)
            x0, y0, x1, y1 = fr.pos
            f3 = [x0, y0, z0, x1, y1, z1]
            cell_id = round(fr.get_attr(FracKeys.id))
            assert 0 <= cell_id < lay.cell_number
            cell = lay.get_cell(cell_id)
            dfn_v3.set_cell(cell, f3, ca_s=CellKeys.s, **CellKeys.kw12)


def get_middle_layer_id(layers):
    layer_n = len(layers)
    if layer_n > 0:
        idx = int(layer_n / 2)
        return idx


def get_middle_layer(layers):
    """
    返回中间的一层.
    """
    layer_n = len(layers)
    if layer_n > 0:
        idx = int(layer_n/2)
        assert idx < layer_n
        return layers[idx]


def create_layers(layer_n):
    """
    创建给定层数的渗流
    """
    assert 0 < layer_n < 300
    layers = []
    while len(layers) < layer_n:
        layers.append(Seepage())
    return layers
