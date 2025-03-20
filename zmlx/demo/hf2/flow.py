"""
流体系统的更新。

边界条件：各个Face的位置的渗透率 (需要从固体体系获得的数据).

处理：流体的注入，流体在裂缝体系内的流动，流体属性的变化，相态的变化等.
     获得压力场.
     为了使得裂缝系统的计算更加稳定，在创建Seepage模型的时候，也应该
     遵循config中定义的方式。
     此模块尽可能基于seepage模块来做，因此，尽可能不要编写新的
     代码。

此模块实现：
    1. 实现一个典型的计算的过程、方法、数据；
    2. 留下可以扩展的接口，处理不同种类流体的定义
       （对于不同的case，主要还是流体的差异）。
"""

from zml import Seepage, SeepageMesh
from zmlx.config import seepage
from zmlx.demo.hf2.dfn import create_dfn
from zmlx.demo.hf2.mesh import create_mesh
from zmlx.demo.hf2.show import show_pre
from zmlx.demo.hf2.solid import create_solid


def create_flow(
        mesh: SeepageMesh,
        fludefs, s,
        p=1.0e6,
        perm=1.0e-14,
        dt_min=1.0, dt_max=24.0 * 3600.0, dv_relative=0.1,
        injectors=None,
        **kw):
    """
    根据固体，创建对应的流体系统模型. 这里，将主要依赖seepage模块来完成. 这样做的好处，从而确保生成的模型
    满足直接在seepage中iterate的要求。
    """
    model = seepage.create(
        mesh=mesh,
        fludefs=fludefs,
        porosity=1.0,  # 全部被流体填充
        pore_modulus=100e6,  # 孔隙刚度
        denc=1.0e5,  # 相对小的热容量
        temperature=285.0,
        p=p,
        s=s,
        perm=perm,
        dt_min=dt_min, dt_max=dt_max, dv_relative=dv_relative,
        injectors=injectors,
        **kw
    )
    return model


def iterate(flow, time_forward, network=None):
    # todo: 根据裂缝的情况，来更新各个face的导流的能力.
    seepage.solve(flow, time_forward=time_forward)


def test_1():
    from zmlx.demo.flow1 import create
    from zmlx import gui
    flow = create()
    gui.execute(func=iterate,
                kwargs=dict(flow=flow, time_forward=3600 * 24 * 30),
                close_after_done=False)


def test_2():
    from zmlx.fluid.ch4 import create as create_ch4
    from zmlx.ui import gui

    fractures = create_dfn()
    network = create_solid(fractures, lave=4)
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
            value=10.0 / 60)
        ],
    )
    print(flow)
    print(f'All fluid volume = {flow.get_fluid_vol(0)}')

    def solve():
        seepage.solve(flow, close_after_done=False,
                      extra_plot=lambda: show_pre(network, flow),
                      time_forward=6000)

    gui.execute(solve, close_after_done=False)


if __name__ == '__main__':
    test_2()
