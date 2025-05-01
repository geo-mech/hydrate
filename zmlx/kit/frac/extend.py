from zml import DDMSolution2, FractureNetwork, Seepage, Tensor2
from zmlx.kit.frac import layer as layer_alg
from zmlx.kit.frac.network import reset_flu_expr
from zmlx.kit.frac.rc3 import set_rc3
from zmlx.kit.frac.reset_pore import reset_pore
from zmlx.kit.frac.set_seepage_topology import set_seepage_topology
from zmlx.kit.frac.update_cond import update_cond


def extend(
        network: FractureNetwork, flow: Seepage,
        sol2: DDMSolution2,
        lave: float,
        va_wmin,
        z_min, z_max, layer_n):
    """
    尝试进行裂缝的扩展.
    Args:
        z_max:
        z_min:
        layer_n:
        va_wmin: 顶点的属性ID，表示这个顶点能够扩展的最小的裂缝宽度
        network:
        flow:
        kic:
        sol2:
        lave:

    Returns:
        None
    """
    # 在尝试扩展之前，要重置裂缝的流体表达式，从而在裂缝扩展之后，建立流体数据的映射.
    reset_flu_expr(network=network)

    # 记录初始的裂缝数量，用于后续判断是否发生了扩展。
    fracture_n = network.fracture_number
    assert fracture_n * layer_n == flow.cell_number, \
        (f'fracture_n * layer_n != flow.cell_number. '
         f'fracture_n = {fracture_n}, '
         f'layer_n = {layer_n}, '
         f'flow.cell_number = {flow.cell_number} ')

    # 对于顶点，更新wmin属性，使得只有确定的顶点才可以扩展
    for vtx in network.vertexes:
        if vtx.fracture_number == 1:
            fracture_i = network.get_fracture(0).index
            # 找到最大的流体压力
            pressure = 0.0
            for layer_i in range(layer_n):
                cell_i = layer_i * fracture_n + fracture_i
                pressure = max(pressure, flow.get_cell(cell_i).pre)
            vtx.set_attr(va_wmin,
                         1.0e-6 if pressure > 10e6 else 1.0e5)

    # 基于DDM和断裂力学，尝试裂缝的扩展
    network.extend_tip(
        kic=Tensor2(xx=1.0, yy=1.0, xy=0.0),  # 一个非常小的值
        sol2=sol2,
        l_extend=lave * 0.3,
        lave=lave,
        va_wmin=va_wmin
    )

    # 在探测到的确发生了扩展之后，去执行进一步的操作
    if network.fracture_number != fracture_n:
        # 将模型恢复为一层层的数据
        discard_faces = []
        layers = layer_alg.split(
            flow, layer_n=layer_n, discard_faces=discard_faces)
        assert len(layers) == layer_n

        backups = [item.get_copy() for item in layers]

        # 建立对应的Cell和Face单元体系(仅创建了结构)
        for idx in range(len(layers)):
            set_seepage_topology(model=layers[idx], network=network)
            assert layers[idx].cell_number == network.fracture_number

        # 恢复各个层的流体
        for layer_i in range(layer_n):
            layer = layers[layer_i]
            for idx in range(layer.cell_number):
                layer.get_cell(idx).set_fluids_by_lexpr(
                    network.get_fracture(idx).flu_expr, backups[layer_i])

        # 将各个层合并为一个模型
        flow.clear_cells_and_faces()
        layer_alg.connect(
            layers,
            result=flow,
            new_face=None if len(discard_faces) == 0 else discard_faces[0]
        )

        # 设置Cell的位置并设置rc3这个属性
        set_rc3(model=flow, network=network, z_min=z_min, z_max=z_max)

        # 更新Cell的Pore
        reset_pore(
            obj=flow,
            v0=flow.get_attr('cell_v0'),
            k=flow.get_attr('cell_k')
        )

        update_cond(
            flow, network
        )

        # 重置Injector的cell_id，因为Cell的次序可能已经发生了改变
        for injector in flow.injectors:
            injector.cell_id = flow.cell_number

        # 在Cell中填充必要的流体 (要避免压力过低的情况)
        for cell in flow.cells:
            assert isinstance(cell, Seepage.Cell)
            target_v = cell.p2v(p=1e3)
            v0 = cell.fluid_vol
            if v0 < target_v:
                dv = target_v - v0
                # 让最前面的这种流体体积增大
                cell.get_fluid(0).vol = dv + cell.get_fluid(0).vol
                print(f'Inject Volume = {dv}')
