from zmlx.base.seepage import as_numpy
from zmlx.base.seepage import get_time
from zmlx.exts.base import Seepage, FractureNetwork
from zmlx.plt.rc3 import show_rc3


def show_pressure(network: FractureNetwork, flow: Seepage, zr=None, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    assert network.fracture_number == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'

    if zr is None:
        zr = [-0.5, 0.5]

    z0, z1 = zr

    rc3 = []
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        x0, y0 = fracture.get_vertex(0).pos
        x1, y1 = fracture.get_vertex(1).pos
        cent = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
        p0 = [x0, y0, (z0 + z1) / 2]
        p1 = [(x0 + x1) / 2, (y0 + y1) / 2, z1]
        rc3.append([*cent, *p0, *p1])

    default_opts = dict(
        cbar=dict(label='The Pressure [MPa]'),
        caption='The Pressure',
        title=f'Time = {get_time(flow, as_str=True)}',
        edge_width=0
    )
    opts = {**default_opts, **opts}
    p = as_numpy(flow).cells.pre / 1e6
    show_rc3(rc3, face_color=p, **opts)
