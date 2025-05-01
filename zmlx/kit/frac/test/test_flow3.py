import math

from zmlx.kit.frac.create_flow import create_flow
from zmlx.kit.frac.network import create_network
from zmlx.geometry.dfn2 import dfn2
from zmlx.kit.frac.plot2 import show_pressure


def test_flow():
    from zmlx.fluid.ch4 import create as create_ch4
    from zmlx.config.seepage import solve

    lave = 3.0
    fractures = dfn2(xr=[-40, 40], yr=[-40, 40], p21=0.3, l_min=2, lr=[10, 60],
                     ar=[0, math.pi * 2])
    network = create_network(fractures=fractures, lave=lave)
    flow = create_flow(
        network=network,
        lave=lave,
        aperture=0.01,
        fludefs=[create_ch4(name='ch4')],
        ini_sat=dict(ch4=1.0),
        pressure=10e6,
        perm=1.0e-12,
        dt_max=10.0,
        z_min=-15, z_max=15, layer_n=1,
        injectors=[dict(
            pos=[0, 0, 0],
            fluid_id=0,
            flu='insitu',
            value=10.0 / 60)
        ],
    )
    solve(flow, close_after_done=False,
          extra_plot=lambda: show_pressure(network, flow, w_min=2),
          time_forward=6000)


if __name__ == '__main__':
    test_flow()
