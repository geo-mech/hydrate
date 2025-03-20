"""
固体系统的更新。

边界条件：裂缝内流体的压力(这是唯一需要从流体系统获得的数据).
计算: 1. 各个位置裂缝的间断位移. 2. 天然的裂缝是否激活.
在这个过程中，不需要去处理裂缝的扩展问题。

此模块基于DDM来计算固体，用于二维/拟三维的裂缝计算。
"""
from zml import FractureNetwork, Seepage, InfMatrix, DDMSolution2
from zmlx.demo.hf2.dfn import create_dfn
from zmlx.demo.hf2.set_insitu_stress import set_insitu_stress
from zmlx.demo.hf2.show import show_ds, show_dn
from zmlx.geometry.dfn2 import get_avg_length


def create_solid(fractures, *, lave=None, thick=100.0):
    """
    创建固体计算的模型. fractures的每一个元素代表一个裂缝，且裂缝fracture是一个长度为4的list，格式为 x0  y0  x1  y1.
    默认的厚度设置为100米，这是储层尺度压裂计算的一个典型的尺寸.
    """
    assert len(fractures) > 0, 'There is no fracture.'

    if lave is None:
        lave = get_avg_length(fractures) / 5.0
        print(f'Use lave = {lave}')

    data = FractureNetwork.FractureData.create(
        h=thick, dn=0, ds=0, f=0.9, p0=1e6, k=0.0)

    network = FractureNetwork()

    for fracture in fractures:
        assert len(fracture) == 4
        network.add_fracture(pos=fracture, lave=lave, data=data)

    return network  # 返回生成的裂缝网络


def test():
    fractures = create_dfn()
    print(f'average length = {get_avg_length(fractures)}')
    network = create_solid(fractures, lave=4)
    print(f'network = {network}')
    show_ds(network)


def iterate(network: FractureNetwork, flow: Seepage, stress, fa_yy, fa_xy, fa_ts,
            fa_keep, matrix: InfMatrix,
            sol2: DDMSolution2, dn_max=0.01, ds_max=0.01):
    """
    对于固体系统。 1、更新已经张开的裂缝的间断位移；2、尝试打开尚未激活的裂缝单元
    """
    assert network.fracture_number == flow.cell_number, 'The number of fractures is not equal to the number of cells.'

    # 在裂缝的内部，设置恒定压力的边界条件
    for idx in range(network.fracture_number):
        fracture = network.get_fracture(idx)
        cell = flow.get_cell(idx)
        pressure = cell.pre
        fracture.p0 = pressure
        fracture.k = 0

    # 设置地应力在各个裂缝上的投影 (如果是None，则在这个函数中，被视为0地应力)
    set_insitu_stress(network=network, stress=stress, fa_yy=fa_yy, fa_xy=fa_xy)

    # 根据裂缝的强度，来确定在计算位移间断的时候是否保留
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.FractureData)
        ts = fracture.get_attr(index=fa_ts, default_val=0.0, left=-1, right=1)
        if ts < 1:  # 强度小于1，则后续应该计算间断位移
            fracture.set_attr(fa_keep, 1)
        else:
            fracture.set_attr(fa_keep, 0)

    # 创建一个子网络，只保留需要计算的部分
    sub_network = network.get_sub_network(fa_key=fa_keep)

    # 更新应力影响矩阵
    matrix.update(sub_network, sol2)

    # 使用最新的矩阵，更新裂缝的位移
    sub_network.update_disp(
        matrix=matrix, fa_yy=fa_yy, fa_xy=fa_xy, dist_max=30,
        gradw_max=1, dn_max=dn_max, ds_max=ds_max)

    # 更新之后，再返回来
    network.copy_fracture_from_sub_network(
        fa_key=fa_keep,
        sub=sub_network)

    # 至此，裂缝的位移计算完成了，下面，要尝试激活那些尚未激活的裂缝单元.


if __name__ == '__main__':
    test()
