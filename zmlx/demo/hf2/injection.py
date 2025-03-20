"""
这里，模拟向二维的裂缝体系内注入流体，在这个过程中，流体在裂缝体系内流动，并且带来各个地方流体压力的变化，进而，可能会带来裂缝缝宽的变化。
但是，这里不考虑裂缝的扩展。因此，网格都是确定的。

创建这个模型，主要的目标，是为后续更加复杂的模型做准备。后续，将压裂分为三个步骤：1、流体；2、固体；3、扩展。这个模块，先不考虑扩展，其
主要的意义，是将另外两个模块（流体和固体），尽可能地调试到比较稳定的状态。

张召彬  2025年3月9日
"""

from zml import InfMatrix, DDMSolution2, Tensor2
from zmlx.demo.hf2.dfn import create_dfn
from zmlx.demo.hf2.flow import create_flow
from zmlx.demo.hf2.mesh import create_mesh
from zmlx.demo.hf2.show import show_dn, show_pre, show_ds
from zmlx.demo.hf2.solid import create_solid
from zmlx.ui import gui
from zmlx.demo.hf2.flow import iterate as flow_iterate
from zmlx.demo.hf2.solid import iterate as solid_iterate


def test_5():
    fractures = create_dfn()
    network = create_solid(fractures, lave=2, thick=100)
    matrix = InfMatrix()
    sol2 = DDMSolution2()
    fa_yy = 0
    fa_xy = 1

    for fracture in network.fractures:
        fracture.p0 = 3e6
        fracture.k = 5e8  # 这个数值是对裂缝开度稳定性的一个约束，数值越大，稳定性约好

    # 更新应力影响矩阵
    matrix.update(network, sol2)

    # 使用最新的矩阵，更新裂缝的位移
    network.update_disp(matrix=matrix, fa_yy=fa_yy, fa_xy=fa_xy,
                        dist_max=50,
                        gradw_max=1,
                        dn_max=0.01, ds_max=0.01)

    show_dn(network)


def test_6():
    from zmlx.fluid.ch4 import create as create_ch4

    fractures = create_dfn()
    network = create_solid(fractures, lave=2, thick=50)
    print(network)

    mesh = create_mesh(network)
    print(mesh)

    flow = create_flow(
        mesh=mesh,
        fludefs=[create_ch4(name='ch4')],
        s=dict(ch4=1.0),
        p=10e6,
        perm=1.0e-12,
        dt_max=10.0,
        injectors=[dict(
            pos=[0, 0, 0],
            fluid_id=0,
            flu='insitu',
            value=10.0 / 60),
        ],
    )

    flow_iterate(flow, time_forward=3000)
    fa_yy = 0
    fa_xy = 1
    fa_ts = 2
    fa_keep = 3
    matrix = InfMatrix()
    sol2 = DDMSolution2()

    stress = Tensor2(xx=-30e6, yy=-20e6)
    solid_iterate(
        network=network, flow=flow, stress=stress,
        fa_yy=fa_yy, fa_xy=fa_xy, fa_ts=fa_ts,
        fa_keep=fa_keep,
        matrix=matrix, sol2=sol2)

    show_pre(network, flow)
    show_dn(network)
    show_ds(network)


if __name__ == '__main__':
    gui.execute(test_6, close_after_done=False)
    # test_6()
