"""
用于二维水力压裂模拟的一些基本的算法.
"""

from zml import FractureNetwork, Seepage, LinearExpr


def set_natural_fractures(network: FractureNetwork,
                          fractures,
                          lave,
                          data=None):
    """导入初始的裂缝网络。

    将裂缝的数据设置为给定的data。当data为None时使用默认参数：
        - 裂缝高度100m
        - 流体压力1MPa
        - 裂缝位置为0

    Args:
        network (FractureNetwork): 需要设置的裂缝网络对象
        fractures: 要添加的裂缝列表
        lave: 裂缝平均长度参数
        data (FractureNetwork.FractureData, optional): 裂缝数据对象，不传时使用默认值

    Returns:
        None
    """
    network.clear()

    if data is None:
        data = FractureNetwork.FractureData.create(
            h=1e2, dn=0, ds=0, f=0.9, p0=1e6, k=0.0)
    else:
        assert isinstance(data,
                          FractureNetwork.FractureData)

    for fracture in fractures:
        assert len(fracture) == 4
        network.add_fracture(pos=fracture, lave=lave, data=data)


def update_topology(flow: Seepage, network: FractureNetwork):
    """更新渗流模型的结构。

    会清除现有cell和face后重新构建网络结构，模型参数将被重置为默认值。

    Args:
        flow (Seepage): 需要更新的渗流模型
        network (FractureNetwork): 裂缝网络对象

    Returns:
        None
    """
    # 首先，清除模型中现有的所有的单元和面
    flow.clear_cells_and_faces()

    # 添加单元
    while flow.cell_number < network.fracture_number:
        flow.add_cell()

    # 添加Face
    for vtx in network.vertexes:
        assert isinstance(vtx, FractureNetwork.Vertex)
        frac_n = vtx.fracture_number
        for i0 in range(frac_n):
            i0x = vtx.get_fracture(i0).index
            for i1 in range(i0 + 1, frac_n):
                i1x = vtx.get_fracture(i1).index
                assert i0x != i1x
                assert i0x < flow.cell_number and i1x < flow.cell_number
                flow.add_face(i0x, i1x)


def update_pos(flow: Seepage, network: FractureNetwork, z=0.0):
    """设置Seepage模型中每个单元格的位置。

    Args:
        flow (Seepage): 需要设置的Seepage模型
        network (FractureNetwork): 裂缝网络对象
        z (float, optional): z轴坐标值，默认为0.0

    Returns:
        None
    """
    for i in range(flow.cell_number):
        pos = network.get_fracture(i).center
        flow.get_cell(i).pos = [pos[0], pos[1], z]


def update_pore(flow: Seepage, network: FractureNetwork,
                base_v0=None, base_k=None):
    """更新孔隙参数。

    Args:
        flow (Seepage): 渗流模型对象
        network (FractureNetwork): 裂缝网络对象
        base_v0 (float, optional): 单位长度裂缝在零压时的基准体积
        base_k (float, optional): 单位长度裂缝的压缩系数（每Pa压力变化引起的体积变化）

    Returns:
        None
    """
    if base_v0 is None or base_k is None:
        return
    assert flow.cell_number == network.fracture_number
    assert base_v0 > 0 and base_k > 0
    for i in range(flow.cell_number):
        length = network.get_fracture(i).length
        c = flow.get_cell(i)
        c.v0, c.k = base_v0 * length, base_k * length


def reset_flu_expr(network: FractureNetwork):
    """重置裂缝网络中每个裂缝的流体表达式。

    Args:
        network (FractureNetwork): 需要重置的裂缝网络

    Returns:
        None
    """
    for f in network.fractures:
        assert isinstance(f, FractureNetwork.Fracture)
        f.flu_expr = LinearExpr.create(index=f.index)


def update_cond(flow: Seepage, network: FractureNetwork, base_g=None,
                exp=3.0):
    """更新导流系数。

    Args:
        flow (Seepage): 渗流模型对象
        network (FractureNetwork): 裂缝网络对象
        base_g (float, optional): 单位长度和单位开度时的基准导流系数
        exp (float, optional): 开度指数（默认3.0对应立方定律）

    Returns:
        None
    """
    if base_g is None:
        return
    assert flow.cell_number == network.fracture_number
    assert base_g > 0

    # 各个裂缝的cond
    vg = [0.0] * network.fracture_number

    for i in range(network.fracture_number):
        fracture = network.get_fracture(i)
        assert isinstance(fracture, FractureNetwork.Fracture)

        length = fracture.length
        assert length > 0

        w = -fracture.dn
        assert w >= 0, f'w = {w}'

        vg[i] = base_g * (max(w, 0.0) ** exp) / length

    # 计算各个Face的cond是两端的裂缝的cond的平均值
    for face in flow.faces:
        assert isinstance(face, Seepage.Face)
        i0, i1 = face.get_cell(0).index, face.get_cell(1).index
        assert i0 < len(vg) and i1 < len(vg)
        face.cond = (vg[i0] + vg[i1]) / 2.0
