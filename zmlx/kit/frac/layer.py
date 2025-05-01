from zml import Seepage


def connect(layers, new_face=None, result=None, face_dir_key='direction'):
    """
    连接多个层的模型，形成一个大的模型。

    Args:
        layers: 需要连接的模型列表
        new_face: 在层之间添加的新的Face的数据
        result: 返回的模型对象
        face_dir_key: 在模型中注册的用于显示flag的名称

    Returns:
        Seepage: 连接后的模型对象

    """
    if not isinstance(result, Seepage):
        result = Seepage()
    else:
        result.clear_cells_and_faces()

    # 注册flag，用以标识Face的类型，1代表层内的face，2代表层间的face
    assert isinstance(face_dir_key, str), 'face_flag must be str'
    fa_dir = result.reg_face_key(key=face_dir_key)

    layer_l = None  # 每一层的cell数量
    for layer in layers:
        assert isinstance(layer, Seepage), \
            f'All layers must be Seepage but got {type(layer)}'

        cell_n0 = result.cell_number

        # 添加Cell
        for c1 in layer.cells:
            assert isinstance(c1, Seepage.Cell)
            result.add_cell(data=c1)

        # 添加Face
        for f1 in layer.faces:
            assert isinstance(f1, Seepage.Face)
            i0 = f1.get_cell(0).index
            i1 = f1.get_cell(1).index
            f2 = result.add_face(
                i0 + cell_n0, i1 + cell_n0, data=f1)
            f2.set_attr(fa_dir, 1)

        # 添加层之间的Face(新建)
        if layer_l is None:
            layer_l = layer.cell_number  # 这是第一层
            assert cell_n0 == 0, \
                'The cell number should be zero before add first layer'
            continue
        else:
            assert layer_l == layer.cell_number, \
                'All layers must have same cell number'
        for i in range(layer_l):
            i2 = cell_n0 + i
            i1 = i2 - layer_l
            assert i1 >= 0, f'i1 must >= 0 but got {i1}'
            f2 = result.add_face(i1, i2, data=new_face)
            f2.set_attr(fa_dir, 2)

    return result


def split(model, layer_n, discard_faces=None):
    """
    将一个模型分割成多个模型。注意，在分割的过程中，层之间的那些Face将会被丢弃

    Args:
        discard_faces: 承接层间的Face
        model: 需要分割的模型
        layer_n: 分割的层数

    Returns:
        list: 分割后的模型列表
    """
    assert isinstance(model, Seepage), 'The given model must be Seepage'
    assert layer_n > 0
    assert model.cell_number % layer_n == 0

    if discard_faces is not None:
        assert isinstance(discard_faces, list), \
            'The given discard_faces must be list'
        discard_faces.clear()

    layers = []

    # 结果初始化
    while len(layers) < layer_n:
        layers.append(Seepage())

    # 每一层的cell数量
    layer_l = model.cell_number // layer_n
    assert layer_l * layer_n == model.cell_number, \
        'The given model cannot be split into given count of layers'

    # 添加Cell
    for cell in model.cells:
        layers[cell.index // layer_l].add_cell(data=cell)

    # 添加Face
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        i0, i1 = face.get_cell(0).index, face.get_cell(1).index
        layer_i0, layer_i1 = i0 // layer_l, i1 // layer_l
        if layer_i0 == layer_i1:
            assert layer_i0 < layer_n
            layers[layer_i0].add_face(
                i0 % layer_l, i1 % layer_l, data=face)
        else:
            if discard_faces is not None:
                discard_faces.append(face.get_copy())

    # 返回结果
    return layers


def test():
    layer = Seepage()
    for i in range(10):
        layer.add_cell()
        if i > 0:
            layer.add_face(i - 1, i)
    print(layer)
    print('-----')

    layers = [layer] * 5
    model = connect(layers)
    print(model)
    print('-----')

    discard_faces = []
    layers = split(model, 5, discard_faces=discard_faces)
    for layer in layers:
        print(layer)
    print('-----')
    print(len(discard_faces))


if __name__ == '__main__':
    test()
