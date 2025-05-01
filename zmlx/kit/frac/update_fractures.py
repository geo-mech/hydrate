from zml import DDMSolution2, InfMatrix, FractureNetwork, Seepage
from zmlx.kit.frac.network import set_aperture_fixed, set_local_stress


def update_fractures(
        network: FractureNetwork, flow: Seepage,
        stress,
        fa_yy, fa_xy, fa_ts, fa_keep,
        matrix: InfMatrix,
        sol2: DDMSolution2,
        layer_n: int,
        dn_max=0.01, ds_max=0.01):
    """
    对于固体系统。 执行如下的操作：
        1. 根据流体的压力，更新裂缝的边界条件；
        2. 根据给定的地应力场，更新裂缝的原位的应力；
        3. 对于尚未激活的裂缝，尝试根据流体压力和应力来激活；
        4. 对于激活的裂缝，更新间断位移dn和ds。

    Args:
        network:
        flow:
        stress:
        fa_yy:
        fa_xy:
        fa_ts:
        fa_keep: 一个临时的裂缝属性，指示在更新位移的时候，是否保留这个裂缝
        matrix:
        sol2:
        layer_n: 模型的层数
        dn_max:
        ds_max:
    """
    fracture_n = network.fracture_number
    assert fracture_n * layer_n == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'

    # 根据流体的体积来设置裂缝的开度
    set_aperture_fixed(network, aperture=0.005)

    # 设置地应力在各个裂缝上的投影 (如果是None，则在这个函数中，被视为0地应力)
    set_local_stress(
        network=network, stress=stress, fa_yy=fa_yy, fa_xy=fa_xy)

    # todo: 修改为正式版。目前为测试功能（仅仅依靠压力来判断是否破裂） 250321
    for fracture_i in range(network.fracture_number):
        fracture = network.get_fracture(fracture_i)
        ts = fracture.get_attr(index=fa_ts, default_val=0.0,
                               left=-1,
                               right=1.0e10,
                               )
        if ts >= 1:
            pressure = 0.0
            for layer_i in range(layer_n):
                cell_i = layer_i * fracture_n + fracture_i
                pressure = max(pressure, flow.get_cell(cell_i).pre)
            if pressure >= ts:
                fracture.set_attr(fa_ts, 0.0)
                print(f'fracture open: fracture_i = {fracture_i}')

    # 根据裂缝的强度，来确定在计算位移间断的时候是否保留
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.FractureData)
        # 裂缝的强度的允许的范围。如果超过了这个范围，则认为强度为0
        ts = fracture.get_attr(index=fa_ts, default_val=0.0,
                               left=-1,
                               right=1.0e10,
                               )
        if ts < 1:  # 强度小于1，则后续应该计算间断位移
            fracture.set_attr(fa_keep, 1)
        else:
            fracture.set_attr(fa_keep, 0)

    # 创建一个子网络，只保留需要计算的部分
    sub_network = network.get_sub_network(fa_key=fa_keep)

    if sub_network.fracture_number > 0:
        # 更新应力影响矩阵
        matrix.update(sub_network, sol2)

        # 使用最新的矩阵，更新裂缝的位移
        sub_network.update_disp(
            matrix=matrix, fa_yy=fa_yy, fa_xy=fa_xy, dist_max=20,
            gradw_max=1, dn_max=dn_max, ds_max=ds_max)

        # 更新之后，再返回来
        network.copy_fracture_from_sub_network(
            fa_key=fa_keep,
            sub=sub_network)
