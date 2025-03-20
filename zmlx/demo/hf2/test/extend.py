from zml import *
from zmlx.alg.get_frac_width import get_frac_width
from zmlx.demo.hf2 import alg


def create(ini_fractures, lave=1.0):
    """
    创建模型:
        导入初始的裂缝网络(初始的dn和ds设置为0);
        根据初始裂缝，建立对应的流体网络:
            建立对应的Cell和Face单元体系
            设置Cell的位置
            建立初始的Pore
            填充流体 (在填充流体之后，各个Cell内就有了压力的定义).
        建立应力影响矩阵(空的矩阵);
        建立DDM的基本解并进行配置;
    """
    sol2 = DDMSolution2()
    matrix = InfMatrix()
    network = FractureNetwork()
    seepage = Seepage()

    # 导入初始的裂缝网络(初始的dn和ds设置为0);
    alg.set_natural_fractures(network=network, fractures=ini_fractures,
                              lave=lave)

    # 建立对应的Cell和Face单元体系(仅创建了结构)
    alg.update_topology(flow=seepage, network=network)

    # 设置Cell的位置.
    alg.update_pos(flow=seepage, network=network,
                   z=0.0)

    # 更新Cell的Pore
    alg.update_pore(flow=seepage, network=network,
                    base_v0=1.0, base_k=0.1e-6)

    # 在Cell中填充必要的流体 (使得初始的压力等于0.1MPa)
    for cell in seepage.cells:
        assert isinstance(cell, Seepage.Cell)
        cell.fluid_number = 1
        v = cell.p2v(p=1e6)
        cell.get_fluid(0).vol = v

    # 返回最终的数据.
    return {'sol2': sol2, 'lave': lave,
            'matrix': matrix,
            'network': network, 'seepage': seepage}


def update_sol(model: dict):
    """
    更新固体:
        根据流体系统内的流体压力来设置裂缝的边界条件(对于裂缝，设置为恒定压力边界);
        更新矩阵;
        更新裂缝的间断位移(dn和ds);
        根据当前的dn和ds，尝试进行裂缝的扩展. 如果裂缝发生了扩展，则:
            更新对应的流体系统的结构.
            更新Cell的位置
            更新Cell的Pore和Pore内部的流体
        否则：
            不需要处理.
    """
    seepage = model.get('seepage')
    assert isinstance(seepage, Seepage)

    network = model.get('network')
    assert isinstance(network, FractureNetwork)

    # 根据流体系统内的流体压力来设置裂缝的边界条件(对于裂缝，设置为恒定压力边界);
    assert seepage.cell_number == network.fracture_number
    for i in range(seepage.cell_number):
        pressure = seepage.get_cell(i).pre
        fracture = network.get_fracture(i)
        assert isinstance(fracture, FractureNetwork.Fracture)
        fracture.p0 = pressure
        fracture.k = 0.0

    # 更新矩阵
    matrix = model.get('matrix')
    assert isinstance(matrix, InfMatrix)

    sol2 = model.get('sol2')
    assert isinstance(sol2, DDMSolution2)

    matrix.update(network=network, sol2=sol2)

    # 更新裂缝的间断位移(dn和ds)
    network.update_disp(matrix=matrix)

    # 根据当前的dn和ds，尝试进行裂缝的扩展
    lave = model.get('lave')

    # 在尝试扩展之前，要重置裂缝的流体表达式，从而在裂缝扩展之后，建立流体数据的映射.
    alg.reset_flu_expr(network=network)

    fracture_n = network.fracture_number
    network.extend_tip(kic=Tensor2(xx=1e6, yy=1e6),
                       sol2=sol2, l_extend=lave * 0.3, lave=lave)

    if network.fracture_number != fracture_n:  # 发生了扩展
        # 建立对应的Cell和Face单元体系(仅创建了结构)
        alg.update_topology(flow=seepage, network=network)

        # 设置Cell的位置.
        alg.update_pos(flow=seepage, network=network,
                       z=0.0)

        # 更新Cell的Pore
        alg.update_pore(flow=seepage, network=network,
                        base_v0=1.0, base_k=0.1e-6)

        # 在Cell中填充必要的流体 (使得初始的压力等于1MPa)
        for cell in seepage.cells:
            assert isinstance(cell, Seepage.Cell)
            cell.fluid_number = 1
            v = cell.p2v(p=1e6)
            if cell.get_fluid(0).vol < v:
                cell.get_fluid(0).vol = v

        print('Extended!')


def update_flu(model: dict):
    """
    更新流体：
        根据最新的裂缝的dn来更新流体系统的导流系数;
        流体系统内流体流动，时间向前推进;
    """
    seepage = model.get('seepage')
    assert isinstance(seepage, Seepage)

    network = model.get('network')
    assert isinstance(network, FractureNetwork)

    # 根据最新的裂缝的dn来更新流体系统的导流系数;
    alg.update_cond(flow=seepage, network=network, base_g=1.0,
                    exp=3.0)

    # 流体系统内流体流动，时间向前推进;
    seepage.iterate(dt=1.0)


def test_1():
    """
    测试模型的创建
    """
    ini_fractures = [(-5, -5, -5, 5),
                     (-5, 5, 5, 5),
                     (-6, 0, 6, 0)]
    model = create(ini_fractures=ini_fractures, lave=1.0)
    print(model)

    seepage = model.get('seepage')
    print(seepage)
    for cell in seepage.cells:
        assert isinstance(cell, Seepage.Cell)
        print(cell.pos, cell.pre, cell.get_fluid(0).vol)

    network = model.get('network')
    print(network)
    for frac in network.fractures:
        assert isinstance(frac, FractureNetwork.Fracture)
        print(frac.pos)


def test_2():
    """
    测试，在恒定的压力下，裂缝的宽度复合预期.
    """
    ini_fractures = [(-5, 0, 5, 0)]
    model = create(ini_fractures=ini_fractures, lave=0.1)
    print(model)

    update_sol(model)

    network = model.get('network')

    sol2 = model.get('sol2')
    assert isinstance(sol2, DDMSolution2)

    for fracture in network.fractures:
        x, y = fracture.center
        width = get_frac_width(x, half_length=5,
                               shear_modulus=sol2.shear_modulus,
                               poisson_ratio=sol2.poisson_ratio,
                               fluid_net_pressure=fracture.p0)
        print(fracture.pos, -fracture.dn, width, fracture.flu_expr)


def test_3():
    """
    测试，在恒定的压力下，裂缝的宽度复合预期.
    """
    ini_fractures = [(-5, 0, 5, 0)]
    model = create(ini_fractures=ini_fractures, lave=1)
    print(model)

    for i in range(20):
        update_sol(model)
        update_flu(model)

    network = model.get('network')

    sol2 = model.get('sol2')
    assert isinstance(sol2, DDMSolution2)

    for fracture in network.fractures:
        x, y = fracture.center
        width = get_frac_width(x, half_length=5,
                               shear_modulus=sol2.shear_modulus,
                               poisson_ratio=sol2.poisson_ratio,
                               fluid_net_pressure=fracture.p0)
        print(fracture.pos, -fracture.dn, width, fracture.flu_expr)


if __name__ == '__main__':
    test_3()
