from zml import FractureNetwork, Seepage
from zmlx.base.seepage import get_time
from zmlx.kit.frac import get_fn2
from zmlx.plt.fig2 import show_fn2
from zmlx.utility.seepage_numpy import as_numpy


def show_ds(network, **opts):
    """
    二维绘图。其中颜色代表ds的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-1)
    tmp = dict(clabel='The shear [m]',
               caption='The Ds',
               w_min=1,
               w_max=5)
    tmp.update(opts)
    show_fn2(pos=pos, w=w, c=c, **tmp)


def show_dn(network, **opts):
    """
    二维绘图。其中颜色代表dn的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-2)
    tmp = dict(clabel='The Normal [m]',
               caption='The Dn',
               w_min=1,
               w_max=5)
    tmp.update(opts)
    show_fn2(pos=pos, w=w, c=c, **tmp)


def show_pressure(network: FractureNetwork, flow: Seepage, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    assert network.fracture_number == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'
    pos, w, c = get_fn2(network)
    c = as_numpy(flow).cells.pre / 1e6
    tmp = dict(clabel='The Pressure [MPa]',
               caption='The Pressure',
               title=f'Time = {get_time(flow, as_str=True)}',
               w_min=1,
               w_max=5)
    tmp.update(opts)
    show_fn2(pos=pos, w=w, c=c, **tmp)
