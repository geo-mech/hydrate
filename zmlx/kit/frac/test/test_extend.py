"""
用以水力压裂计算的辅助函数。
"""

from zml import DDMSolution2, InfMatrix, Tensor2, Coord3
from zmlx import AttrKeys
from zmlx.kit.frac.create_flow import create_flow
from zmlx.kit.frac.extend import extend
from zmlx.kit.frac.network import create_network
from zmlx.kit.frac.update_cond import update_cond
from zmlx.kit.frac.update_fractures import update_fractures
from zmlx.config.seepage import set_dt, get_dt, solve
from zmlx.fluid.ch4 import create as create_ch4
from zmlx.kit.frac.plot2 import show_pressure, show_dn, show_ds
from zmlx.kit.frac.plot3 import show_pressure as show_pressure3d
from zmlx.ui import gui


def test_extend():
    z_min, z_max = -15.0, 15.0  # 模型的z轴范围
    layer_n = 1  # 在z方向上的层数(目前的测试，其实还是2维的)
    height = z_max - z_min  # 模型的高度
    lave = 3  # 单元的长度

    fractures = [[-3, -5, -3, 5], [3, -5, 3, 5]]
    # 创建裂缝网络，我们的流体是3维的，但是裂缝网络仍然是2维的
    network = create_network(fractures, lave=lave, height=height)
    print(network)

    # 管理裂缝和顶点的属性ID
    fa = AttrKeys()
    va = AttrKeys()
    # 用于应力计算的参数
    matrix = InfMatrix()
    sol2 = DDMSolution2()
    stress = Tensor2(xx=-20e6, yy=-21e6, xy=0)
    coord = Coord3()

    # 设置各个裂缝的强度属性
    for fracture in network.fractures:
        fracture.set_attr(fa.ts, 10e6)

    flow = create_flow(
        network=network,
        fludefs=[create_ch4(name='ch4')],
        ini_sat=dict(ch4=1.0),
        lave=lave,
        z_min=z_min, z_max=z_max,
        layer_n=layer_n,
        aperture=0.01,
        pressure=10e6,
        perm=1.0e-12,
        dt_min=1.0e-5,  # 最小允许的dt，这个很重要
        dt_max=10.0,
        dv_relative=0.05,
        injectors=[
            dict(
                pos=[-3, 0, 0],
                fluid_id=0,
                flu='insitu',
                value=1.0 / 60),
            dict(
                pos=[3, 0, 0],
                fluid_id=0,
                flu='insitu',
                value=1.0 / 60),
        ],
        network_coord=coord,
    )

    def run():
        for step in range(300):
            update_fractures(
                network=network, flow=flow, stress=stress,
                fa_yy=fa.yy, fa_xy=fa.xy, fa_ts=fa.ts,
                fa_keep=fa.keep,
                matrix=matrix,
                sol2=sol2,
                layer_n=layer_n,
            )

            update_cond(
                flow, network,
                relax_factor=0.02,
                g_times_max=20.0,
                aperture_max=0.01,
            )

            set_dt(flow, get_dt(flow) * 0.01)
            solve(flow, time_forward=5)

            extend(
                network=network, flow=flow, va_wmin=va.wmin,
                sol2=sol2,
                lave=lave,
                z_min=z_min, z_max=z_max, layer_n=layer_n
            )

            show_pressure(network, flow)
            show_dn(network)
            show_ds(network)
            show_pressure3d(flow)

    gui.execute(func=run, close_after_done=False,
                disable_gui=0
                )


if __name__ == '__main__':
    test_extend()
