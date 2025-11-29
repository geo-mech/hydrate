from zmlx.base.frac import get_fn2
from zmlx.base.seepage import as_numpy, get_time
from zmlx.exts.base import FractureNetwork, Seepage
from zmlx.plt.fig2 import show_fn2


def show_ds(network, **opts):
    """
    二维绘图。其中颜色代表ds的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-1)
    default_opts = dict(
        cbar=dict(label='The shear [m]'),
        caption='The Ds',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)


def show_dn(network, **opts):
    """
    二维绘图。其中颜色代表dn的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-2)
    default_opts = dict(
        cbar=dict(label='The normal [m]'),
        caption='The Dn',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)


def show_pressure(network: FractureNetwork, flow: Seepage, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    assert network.fracture_number == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'
    pos, w, c = get_fn2(network)
    c = as_numpy(flow).cells.pre / 1e6
    default_opts = dict(
        cbar=dict(label='The Pressure [MPa]'),
        caption='The Pressure',
        title=f'Time = {get_time(flow, as_str=True)}',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)
