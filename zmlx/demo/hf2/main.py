from collections.abc import Iterable

from zml import Seepage, InfMatrix, DDMSolution2, Tensor2, FractureNetwork
from zmlx.config import seepage
from zmlx.config.frac import get_fn2
from zmlx.demo.hf2.alg import set_natural_fractures, update_topology, update_pos, update_pore, reset_flu_expr, \
    update_cond
from zmlx.plt.show_fn2 import show_fn2
from zmlx.ui.GuiBuffer import gui


def initialize(flow: Seepage, network: FractureNetwork,
               fractures: Iterable, lave: float):
    """
    初始化
    """
    # 导入初始的裂缝网络(初始的dn和ds设置为0);
    set_natural_fractures(network=network, fractures=fractures,
                          lave=lave)

    # 建立对应的Cell和Face单元体系(仅创建了结构)
    update_topology(flow=flow, network=network)

    # 设置Cell的位置.
    update_pos(flow=flow, network=network, z=0.0)

    # 更新Cell的Pore
    update_pore(flow=flow, network=network, base_v0=1.0, base_k=0.1e-6)

    # 在Cell中填充必要的流体 (使得初始的压力等于0.1MPa)
    for cell in flow.cells:
        cell.fluid_number = 1
        v = cell.p2v(p=1e2)
        cell.get_fluid(0).vol = v


def iterate(flow: Seepage, network: FractureNetwork,
            matrix: InfMatrix, sol2: DDMSolution2,
            lave: float):
    """
    更新固体
    """
    # 根据流体系统内的流体压力来设置裂缝的边界条件(对于裂缝，设置为恒定压力边界);
    assert flow.cell_number == network.fracture_number
    for i in range(flow.cell_number):
        fracture = network.get_fracture(i)
        fracture.p0 = flow.get_cell(i).pre
        fracture.k = 0.0

    matrix.update(network=network, sol2=sol2)

    # 更新裂缝的间断位移(dn和ds)
    network.update_disp(matrix=matrix)

    # 在尝试扩展之前，要重置裂缝的流体表达式，从而在裂缝扩展之后，建立流体数据的映射.
    reset_flu_expr(network=network)

    fracture_n = network.fracture_number
    network.extend_tip(kic=Tensor2(xx=1e6, yy=1e6),
                       sol2=sol2,
                       l_extend=lave * 0.3, lave=lave)

    if network.fracture_number != fracture_n:
        print('Extended!')

        backup = flow.get_copy()

        # 建立对应的Cell和Face单元体系(仅创建了结构)
        update_topology(flow=flow, network=network)
        assert flow.cell_number == network.fracture_number
        for idx in range(flow.cell_number):
            cell = flow.get_cell(idx)
            frac = network.get_fracture(idx)
            cell.set_fluids_by_lexpr(frac.flu, backup)  # 恢复流体

        # 设置Cell的位置.
        update_pos(flow=flow, network=network, z=0.0)

        # 更新Cell的Pore
        update_pore(
            flow=flow, network=network, base_v0=1.0, base_k=0.1e-6)

        for injector in flow.injectors:
            assert isinstance(injector, Seepage.Injector)
            injector.cell_id = flow.cell_number

        # 在Cell中填充必要的流体 (使得初始的压力等于1MPa)
        for cell in flow.cells:
            cell.fluid_number = 1
            v = cell.p2v(p=1e2)
            if cell.get_fluid(0).vol < v:
                cell.get_fluid(0).vol = v

    # 根据network的最新的状态，去更新流体系统
    update_cond(flow=flow, network=network, base_g=1.0, exp=3.0)
    if True:
        for x in [-2, 2]:
            cell = flow.get_nearest_cell(pos=[x, 0, 0])
            v = cell.p2v(p=5e6)
            if cell.get_fluid(0).vol < v:
                print(f'vol = {cell.get_fluid(0).vol}  ->  {v}')
                cell.get_fluid(0).vol = v
    seepage.iterate(model=flow, dt=10)


def main():
    sol2 = DDMSolution2()
    matrix = InfMatrix()
    network = FractureNetwork()
    flow = Seepage()
    lave = 1.0

    initialize(flow=flow, network=network,
               fractures=[(-2, -2, -2, 2),
                          (2, -2, 2, 2)],
               lave=lave)

    for i in range(100):
        print(f'step = {i}')
        iterate(flow=flow, network=network, matrix=matrix, sol2=sol2, lave=lave)
        pos, w, c = get_fn2(network=network)
        if i % 10 == 0:
            show_fn2(pos=pos, w=w, c=c, caption='裂缝', clabel='Width',
                     gui_only=True)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False, disable_gui=False)
