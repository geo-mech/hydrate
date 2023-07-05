# -*- coding: utf-8 -*-
"""
定义数据格式 fn2，主要包括4列数据，用于定义裂缝位置，1列数据，用于定义裂缝的宽度，
1列数据，用于定义裂缝的颜色（如压力）
"""


from zml import is_array, gui
from zmlx.plt.plot2 import plot2
from zmlx.plt.get_color import get_color
import warnings


try:
    import numpy as np
except Exception as err:
    np = None
    warnings.warn(f'warning. file: {__file__}. msg: {err}')


def from_network2(network=None, seepage=None, ca_c=None, fa_id=None, fa_c=None):
    """
    对于颜色:
        将首先从裂缝的fa_c属性中获得，如果获得失败，则从seepage的Cell的ca_c属性获得.
    返回：
        裂缝的位置，缝宽，颜色
    """
    pos = []
    w = []
    c = []
    if network is not None:
        for fracture in network.get_fractures():
            pos.append(fracture.pos)
            w.append(-fracture.dn)
            if fa_c is not None:
                tmp = fracture.get_attr(index=fa_c)
                if tmp is not None:
                    c.append(tmp)
                    continue
            if ca_c is not None and seepage is not None and fa_id is not None:
                cell_id = round(fracture.get_attr(fa_id))
                if cell_id < seepage.cell_number:
                    tmp = seepage.get_cell(cell_id).get_attr(ca_c)
                    if tmp is not None:
                        c.append(tmp)
                        continue
            c.append(-fracture.dn)
    return pos, w, c


def show_fn2(pos=None, w=None, c=None, w_max=4, network=None, seepage=None,
             ca_c=None, fa_id=None, fa_c=None, ipath=None, **kwargs):
    """
    显示二维裂缝网络数据。其中：
        pos包含4列，为各个线段的位置
        w为各个线条的宽度（原始数据）
        c为各个线条的颜色（原始数据）
        wmax为画图的时候线条的最大宽度
    对于颜色:
        将首先从裂缝的fa_c属性中获得，如果获得失败，则从seepage的Cell的ca_c属性获得.
    """
    if pos is None or w is None or c is None:
        if network is not None:
            pos, w, c = from_network2(network=network, seepage=seepage, ca_c=ca_c, fa_id=fa_id, fa_c=fa_c)

    if pos is None or w is None or c is None:
        if ipath is not None and np is not None:
            d = np.loadtxt(ipath)
            pos = d[:, 0:4]
            w = d[:, 4]
            c = d[:, 6]

    count = len(pos)
    if count == 0:
        return

    assert not is_array(w) or len(w) == count
    assert not is_array(c) or len(c) == count

    def get(t, i):
        if is_array(t):
            return t[i]
        else:
            return t if t is not None else 1

    def get_w(i):
        return get(w, i)

    def get_c(i):
        return get(c, i)

    def get_r(f):
        """
        返回给定函数的取值范围
        """
        lr = f(0)
        rr = lr
        for i in range(1, count):
            v = f(i)
            lr = min(lr, v)
            rr = max(rr, v)
        return lr, rr

    # 宽度和颜色对应的原始数据的范围
    wl, wr = get_r(get_w)
    cl, cr = get_r(get_c)
    xl, xr = get_r(lambda i: (pos[i][0] + pos[i][2]) / 2)
    yl, yr = get_r(lambda i: (pos[i][1] + pos[i][3]) / 2)

    # 获取颜色表
    cmap = kwargs.pop('cmap', None)
    if cmap is None:
        from matplotlib import cm
        cmap = cm.coolwarm

    data = []
    for idx in range(count):
        x0, y0, x1, y1 = pos[idx]
        data.append({'name': 'plot', 'args': [[x0, x1], [y0, y1]],
                     'kwargs':
                         {'c': get_color(cmap, cl, cr, get_c(idx)),
                          'linewidth': 0.1 + get_w(idx) * w_max / max(wr, 1.0e-10)}
                     })

    # 在中心点画一个小三角形，用以显示颜色
    xc = (xl + xr) / 2
    yc = (yl + yr) / 2
    xw = xr - xl
    yw = yr - yl
    data.append({'name': 'tricontourf', 'has_colorbar': True, 'kwargs': {
        'x': [xc, xc + xw / 1e6, xc],
        'y': [yc, yc, yc + yw / 1e6],
        'z': [cl, (cl + cr) / 2, cr],
        'levels': 10}})

    kwargs['aspect'] = 'equal'
    plot2(data=data,  **kwargs)


def test():
    from zmlx.data.example_fn2 import pos, w, c
    gui.execute(lambda: show_fn2(pos, w, c), close_after_done=False)


if __name__ == '__main__':
    test()
