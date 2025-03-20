from zml import FractureNetwork, Seepage
from zmlx.config import seepage
from zmlx.config.frac import get_fn2
from zmlx.plt.show_fn2 import show_fn2
from zmlx.utility.SeepageNumpy import as_numpy


def show_ds(network, **opt):
    """
    绘图。其中颜色代表ds的值. 主要用于测试.
    """
    pos, w, c = get_fn2(network, key=-1)
    if opt.get('clabel') is None:
        opt['clabel'] = 'The shear [m]'
    if opt.get('caption') is None:
        opt['caption'] = 'The Ds'
    show_fn2(pos=pos, w=w, c=c, **opt)


def show_dn(network, **opt):
    """
    绘图。其中颜色代表ds的值. 主要用于测试.
    """
    pos, w, c = get_fn2(network, key=-2)
    if opt.get('clabel') is None:
        opt['clabel'] = 'The Normal [m]'
    if opt.get('caption') is None:
        opt['caption'] = 'The Dn'
    show_fn2(pos=pos, w=w, c=c, **opt)


def show_pre(network: FractureNetwork, flow: Seepage, **opt):
    """
    绘图。其中颜色代表ds的值. 主要用于测试.
    """
    assert network.fracture_number == flow.cell_number, 'The number of fractures is not equal to the number of cells.'
    pos, w, c = get_fn2(network)
    c = as_numpy(flow).cells.pre / 1e6
    # 设置默认值
    if opt.get('clabel') is None:
        opt['clabel'] = 'The Pressure [MPa]'
    if opt.get('title') is None:
        time = seepage.get_time(flow, as_str=True)
        opt['title'] = f'Time = {time}'
    if opt.get('caption') is None:
        opt['caption'] = 'The Pressure'
    show_fn2(pos=pos, w=w, c=c, w_min=1, w_max=5, **opt)
