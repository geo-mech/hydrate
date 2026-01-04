"""
基于分层三维的压裂计算模型
"""

import random

from zmlx.exts import DDMSolution2, InfMatrix
from zmlx.geometry.dfn2 import dfn2
from zmlx.scen.frac._base import *
from zmlx.scen.frac._layered import create as create_layered, create_fracture_virtual_groups
from zmlx.scen.frac._show import *
from zmlx.scen.frac._wmin import update_wmin
from zmlx.tfc.groups import iterate as iterate_layered
from zmlx.ui import gui, progress, show_attrs, break_point
from zmlx.utility import AttrKeys


def create(
        box3: Optional[List[float]] = None,
        vx_inj: Optional[List[float]] = None,
        l_ave: float = 4.0,
        q_inj: float = 1.0,
        in_situ_stress: Optional[Tensor2] = None,
        fa: Optional[AttrKeys] = None,
        va: Optional[AttrKeys] = None,
        sol2: Optional[DDMSolution2] = None,
        step_max: Optional[int] = None,
        dfn_opts: Optional[List[Dict[str, Any]]] = None,
        layered_opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    建模。将模型的一切变量都通过参数的形式在这里给出。

    Args:
        l_ave: 主裂缝单元的长度。 用以控制计算网格的精度。默认值为3.0
        box3: 存储层的3D盒子，格式为 [x_min, x_max, y_min, y_max, z_min, z_max]
        vx_inj: 注入点的x坐标，格式为 [x1, x2, ..., xn]
        q_inj: 注入流量，默认值为1.0 (单位：m³/s)
        in_situ_stress: 地应力，默认值为 Tensor2(xx=-10e6, yy=-12e6, xy=0)
        fa: 自动管理裂缝的属性ID，默认值为 None
        va: 自动管理Vertex的属性ID，默认值为 None
        sol2: 二维DDM的基本解，默认值为 None
        step_max: 最大迭代次数，默认值为 None，即不限制迭代次数
        dfn_opts: 创建DFN的选项, 默认为None
        layered_opts: 创建分层模型的选项. 默认为None
    Returns:
        建立的模型
    """
    if box3 is None:
        box3 = [-50.0, 50.0, -200.0, 200.0, -20.0, 20.0]
    else:
        assert len(
            box3) == 6, f'box3d must be a list of 6 elements (format: [x_min, x_max, y_min, y_max, z_min, z_max]), but got {len(box3)}'

    # 获取计算的范围
    x_min, x_max, y_min, y_max, z_min, z_max = box3
    print(f'box3d = {box3}')
    assert 20.0 <= x_max - x_min <= 150.0
    assert 100.0 <= y_max - y_min <= 600.0
    assert 10.0 <= z_max - z_min <= 100.0

    # 获取初始射孔簇的x坐标(注意，默认y坐标等于0，z坐标等于0)
    # 另外，假设流体从左侧注入.
    # 务必注意此局部坐标系的定义。
    if vx_inj is None:
        vx_inj = [-10.0, -3, 3, 10.0]
    else:
        assert len(vx_inj) > 0, f'vx_inj must be a list of at least 1 element, but got {len(vx_inj)}'
    assert x_min < min(vx_inj) <= max(
        vx_inj) < x_max, f'vx_inj must be in the range of {x_min} to {x_max}, but got {vx_inj}'
    print(f'vx_inj = {vx_inj}')

    # 主裂缝单元的长度
    assert 1.0 <= l_ave <= 10.0, f'l_ave must be in the range of 1.0 to 10.0, but got {l_ave}'

    # 原始地应力(二维应力场)
    if in_situ_stress is None:
        in_situ_stress = Tensor2(xx=-10e6, yy=-12e6, xy=0)
    if fa is None:
        fa = AttrKeys()
    if va is None:
        va = AttrKeys()
    if sol2 is None:
        sol2 = DDMSolution2()

    if dfn_opts is not None:
        dfn_data = dfn2(dfn_opts, xr=[x_min, x_max], yr=[y_min, y_max], l_min=3)
    else:
        dfn_data = []

    if len(dfn_data) > 0 and layered_opts is None:
        layered_opts = dict()  # 给定了DFN，这样，确保创建分层模型

    if layered_opts is not None:
        fractures = [{'trajectory': f, 'perm_h': 1e-9 * random.uniform(0.01, 0.8), 'perm_v': 1e-11} for f in dfn_data]
        jx = round((x_max - x_min) / l_ave)
        jy = round((y_max - y_min) / (l_ave * 1.5))
        jz = round((z_max - z_min) / l_ave)

        opts = dict(
            x0=x_min, x1=x_max, y0=y_min, y1=y_max, z0=z_min, z1=z_max,
            jx=jx, jy=jy, jz=jz,
            dt=10.0,
            fractures=fractures,
            perm=1.0e-14,
            dfn2_data=dfn_data,
            bound_open=False
        )
        opts.update(layered_opts)
        layered_model = create_layered(**opts)
        print(f'layered_model = {layered_model}')
    else:
        layered_model = None

    # 创建初始裂缝网络，后续，将在此基础上更新
    network = FractureNetwork()
    network.add_fracture(first=[min(vx_inj) - l_ave, 0.0], second=[max(vx_inj), 0.0], lave=l_ave)
    for x in vx_inj:
        network.add_fracture(first=[x, -5.0], second=[x, 5.0], lave=l_ave)

    inf_matrix = InfMatrix()  # 应力影响矩阵
    if step_max is None:
        step_max = 250

    return dict(
        q_inj=q_inj, step_max=step_max, network=network, fa=fa, va=va, in_situ_stress=in_situ_stress,
        z_min=z_min, z_max=z_max, inf_matrix=inf_matrix, vx_inj=vx_inj, l_ave=l_ave, sol2=sol2,
        layered_model=layered_model,
    )


def _update_disp(network: FractureNetwork, inf_matrix: InfMatrix, fa: AttrKeys, in_situ_stress, z_max: float,
                 z_min: float,
                 sol2: DDMSolution2, **_):
    """
    更新裂缝的间断位移
    """
    # todo:
    #     目前，应力场设置的是一个数值，后续，可以是非均值的(不是迫切需求). 另外，这里的应力，其实是各个层的平均的应力，
    #     需要根据三维的应力去计算
    set_local_stress(network, fa_yy=fa.yy, fa_xy=fa.xy, global_stress=in_situ_stress)

    # todo:
    #     根据实际的高度来设置h属性（依托基于多层渗流的计算体系）
    set_h(network, z_max - z_min)

    # 更新应力影响矩阵（用于建立边界元方程）
    inf_matrix.update(network=network, sol2=sol2)

    # 更新裂缝内的流体压力 todo: 使用真实的渗流压力（也需要根据多层的压力来平均）
    # 说明：
    #    此处，虽然说定压力，但是，也给定了较大的k，使得本身具有较大的刚度
    set_p_fixed(network, p=15e6, w=0.001, k=1e8)

    # 更新裂缝的间断位移
    network.update_disp(matrix=inf_matrix, fa_xy=fa.xy, fa_yy=fa.yy)


def _extend(network: FractureNetwork, sol2: DDMSolution2, l_ave: float, va: AttrKeys, fa: AttrKeys, vx_inj: List[float],
            q_inj: float, **_):
    """
    扩展裂缝尖端
    """
    # 更新裂缝扩展的临界流体压力（根据最新的间断位移，计算此时的应力。在此基础上，结合强度和原始应力）
    set_vertex_attr(network, index=va.pc, value=1.0)
    for v1 in network.vertexes:
        if v1.fracture_number == 1:
            v0 = v1.get_vertex(0)
            assert v0 is not None
            x0, y0 = v0.pos
            x1, y1 = v1.pos
            x2 = x1 * 2 - x0
            y2 = y1 * 2 - y0
            stress = network.get_induced(pos=[x1, y1, x2, y2], sol2=sol2)
            pc = -stress.yy  # todo: 考虑岩石强度+初始地应力
            set_vertex_attr(v1, index=va.pc, value=pc)

    # todo: 需要根据流体的实际阻力来设置
    set_fracture_attr(network, index=fa.resist, value=1.0e6)
    for f in network.fractures:
        x, y = f.center
        if abs(y) < 0.1:
            f.set_attr(index=fa.resist, value=1e2)
        elif abs(y) < 10:
            f.set_attr(index=fa.resist, value=1e7)

    # 有了以上关于流动阻力和应力/强度条件的设置，在这里，评估在哪个尖端能够扩展
    update_wmin(network, x_inj=min(vx_inj) - l_ave, y_inj=0, q_inj=q_inj, va_wmin=va.wmin,
                fa_resist=fa.resist, va_pc=va.pc, dist_min=l_ave)

    clamp_width(network, left=1.0e-4)  # 确保标记了wmin的地方都能够扩展

    # 尖端扩展(根据wmin来判断是否能够扩展)
    kic = Tensor2(xx=1, yy=1, xy=0.0)  # 在这里，将kic设置为一个非常小的数值，也就是不基于此来控制尖端的扩展
    network.extend_tip(kic=kic, sol2=sol2, l_extend=l_ave, va_wmin=va.wmin, angle_max=0.6, lave=l_ave)


def _iterate_flow(network: FractureNetwork, vx_inj: List[float], layered_model: Optional[Dict[str, Any]], **_):
    """
    更新流体系统(热流化体系)
    """
    if layered_model is None:
        return

    fractures = [
        dict(
            network=network, perm_h=1.0e-9, perm_v=1.0e-11, injectors=[
                dict(
                    pos=[min(vx_inj), 0.0, 0.0], fluid_name='water', rate=1.0e-1
                )
            ]
        )
    ]
    layers: List[Seepage] = layered_model['layers']
    groups: List[Dict[str, Any]] = layered_model['groups']

    virtual_groups: List[Dict[str, Any]] = create_fracture_virtual_groups(layers=layers, fractures=fractures)
    group_n = len(groups)
    groups.extend(virtual_groups)

    for times in range(10):
        iterate_layered(layered_model)
    groups = groups[:group_n]
    layered_model['groups'] = groups


def iterate(space: Dict[str, Any]):
    """
    向前迭代一步。执行在一次迭代中的所有的操作。
    """
    # 更新裂缝的间断位移
    _update_disp(**space)

    # 尖端扩展
    _extend(**space)

    # 将裂缝网络添加到layered模型中，然后迭代layered模型
    _iterate_flow(**space)


def _display(step: int, step_max: int, network: FractureNetwork, **_):
    """
    尝试在打印一些提示信息
    """
    show_attrs(
        step=dict(name='迭代步数', value=step),
        fracture_n=dict(name='裂缝数量', value=network.fracture_number),
        vertex_n=dict(name='顶点数量', value=network.vertex_number)
    )
    show_p_range(network)
    show_w_range(network)
    show_ds_range(network)
    progress(label='计算进度', val_range=[0, step_max], value=step)


def _plot(network: FractureNetwork, layered_model: Optional[Dict[str, Any]], **_):
    """
    尝试在界面绘图
    """
    if gui.exists():
        show_network(network, w_min=0.5, w_max=3)
        if layered_model is not None:
            f = layered_model.get('show')
            if f is not None:
                f()


def solve(space: Dict[str, Any]):
    """
    执行求解
    """
    from zmlx.utility import GuiIterator
    it = GuiIterator(iterate=iterate, plot=lambda: _plot(**space))
    for step in range(space['step_max']):
        break_point()
        it(space)
        _display(step=step, **space)


def execute(gui_mode: bool = True, **opts):
    """
    建模并执行求解。将模型的一切变量都通过参数的形式在这里给出。
    """
    space = create(**opts)
    if gui_mode:
        gui.execute(lambda: solve(space), close_after_done=False)
    else:
        solve(space)
