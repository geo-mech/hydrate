from zml import Seepage, FractureNetwork
from zmlx.config import attr_keys


def set_rc3(model: Seepage, network: FractureNetwork, z_min, z_max):
    """
    设置模型各个cell的三维矩形的坐标(包括cell的pos属性)。主要用于后续的绘图

    Args:
        model: 需要设置的模型
        network: 模型对应的裂缝网络，注意，模型中cell的数量，必须是network.fracture_number的整数倍
        z_min: z坐标的最小值
        z_max: z坐标的最大值

    Returns:
        None
    """
    fracture_n = network.fracture_number
    assert fracture_n > 0
    assert model.cell_number % fracture_n == 0
    layer_n = model.cell_number // network.fracture_number
    assert network.fracture_number * layer_n == model.cell_number
    layer_h = (z_max - z_min) / layer_n

    ca = attr_keys.cell_keys(model)
    ca_x1 = ca.x1
    ca_y1 = ca.y1
    ca_z1 = ca.z1
    ca_x2 = ca.x2
    ca_y2 = ca.y2
    ca_z2 = ca.z2

    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x0, y0, x1, y1 = network.get_fracture(cell.index % fracture_n).pos
        z = z_min + layer_h * (cell.index // fracture_n + 0.5)
        cell.pos = [(x0 + x1) / 2, (y0 + y1) / 2, z]
        cell.set_attr(ca_x1, x1)
        cell.set_attr(ca_y1, y1)
        cell.set_attr(ca_z1, z)
        cell.set_attr(ca_x2, (x0 + x1) / 2)
        cell.set_attr(ca_y2, (y0 + y1) / 2)
        cell.set_attr(ca_z2, z + layer_h / 2)


def get_rc3(model: Seepage):
    """
    获取模型各个cell的三维矩形的坐标。主要用于后续的绘图
    Args:
        model: 需要设置的模型
    Returns:
        模型各个cell的三维矩形的坐标
    """
    ca = attr_keys.cell_keys(model)
    ca_x1 = ca.x1
    ca_y1 = ca.y1
    ca_z1 = ca.z1
    ca_x2 = ca.x2
    ca_y2 = ca.y2
    ca_z2 = ca.z2
    return [
        [*cell.pos,
         cell.get_attr(ca_x1), cell.get_attr(ca_y1), cell.get_attr(ca_z1),
         cell.get_attr(ca_x2), cell.get_attr(ca_y2), cell.get_attr(ca_z2)]
        for cell in model.cells
    ]


def test():
    network = FractureNetwork()
    network.add_fracture([0, 0], [1, 1], lave=0.1)
    model = Seepage()
