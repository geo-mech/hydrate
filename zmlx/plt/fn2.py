"""
定义数据格式 fn2，主要包括4列数据，用于定义裂缝位置，1列数据，用于定义裂缝的宽度，
1列数据，用于定义裂缝的颜色（如压力）
"""

from zml import is_array
from zmlx.plt.cmap import get_cm, get_color


def add_fn2(
        ax, *, pos=None, w=None, c=None, w_min=1, w_max=4, cmap=None, clim=None, wlim=None, cbar=None,
        fn2_aspect=None):
    """
    在ax上添加fn2数据
    """
    count = len(pos)
    if count == 0:
        return

    assert not is_array(w) or len(w) == count, f'w = {w}, count = {count}'
    assert not is_array(c) or len(c) == count, f'c = {c}, count = {count}'

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
        lr = f(0)
        rr = lr
        for i in range(1, count):
            v = f(i)
            lr = min(lr, v)
            rr = max(rr, v)
        return lr, rr

    # 宽度和颜色对应的原始数据的范围
    if wlim is None:
        wl, wr = get_r(get_w)
    else:
        assert len(wlim) == 2, f"wlim = {wlim}"
        wl, wr = wlim

    if clim is None:
        cl, cr = get_r(get_c)
    else:
        assert len(clim) == 2, f"clim = {clim}"
        cl, cr = clim

    cmap = get_cm(cmap)

    if w_max < w_min:  # 确保w_max > w_min
        w_max, w_min = w_min, w_max

    for idx in range(count):
        x0, y0, x1, y1 = pos[idx]
        lw = w_min + get_w(idx) * (w_max - w_min) / max(wr, 1.0e-10)
        ax.plot([x0, x1], [y0, y1],
                c=get_color(cmap, cl, cr, get_c(idx)),
                linewidth=lw)

    if cbar is not None:
        from zmlx.plt.cbar import add_cbar
        add_cbar(ax, cmap=cmap, clim=[cl, cr], **cbar)

    if fn2_aspect is not None:
        xl, xr = get_r(lambda i: (pos[i][0] + pos[i][2]) / 2)
        yl, yr = get_r(lambda i: (pos[i][1] + pos[i][3]) / 2)
        ratio = max(xr - xl, 1.0e-10) / max(yr - yl, 1.0e-10)
        if 0.0333 <= ratio <= 33.33:
            ax.set_aspect(fn2_aspect)


def show_fn2(
        pos=None, w=None, c=None, w_min=1, w_max=4, ipath=None, iw=4, ic=6,
        clabel=None, ctitle=None, cbar=None,
        title=None,
        xlabel=None, ylabel=None,
        xlim=None, ylim=None,
        **opt
):
    """显示二维裂缝网络数据。

    该函数支持两种数据输入方式：
    1. 直接通过参数传递数据
    2. 从文本文件读取数据（当ipath参数被指定时）

    Args:
        pos (list[tuple], optional): 裂缝位置数据，每个元素为包含4个浮点数的元组，
            表示线段端点坐标(x0, y0, x1, y1)。默认为None。
        w (list[float], optional): 裂缝宽度数据，长度需与pos一致。默认为None。
        c (list[float], optional): 裂缝颜色数据，长度需与pos一致。默认为None。
        w_min: (float, optional): 线条最小显示宽度（像素单位）。默认为0.1。
        w_max (float, optional): 线条最大显示宽度（像素单位）。默认为4。
        ipath (str, optional): 数据文件路径，优先级高于pos/w/c参数。默认为None。
        iw (int, optional): 文件中宽度数据列索引（0-based）。默认为4。
        ic (int, optional): 文件中颜色数据列索引（0-based）。默认为6。
        clabel (str, optional): 颜色条轴标签（如'Pressure [Pa]'）。默认为None。
        ctitle (str, optional): 颜色条标题。默认为None。
        title (str, optional): 图表主标题。默认为None。
        cbar (dict, optional): 颜色条参数，包含'label'和'title'键。默认为None。
        xlabel (str, optional): x轴标签，默认显示'x / m'。
        ylabel (str, optional): y轴标签，默认显示'y / m'。
        xlim (tuple[float], optional): x轴显示范围(min, max)。默认为None。
        ylim (tuple[float], optional): y轴显示范围(min, max)。默认为None。
        **opt: 传递给 plot 的额外参数

    Returns:
        None: 直接显示matplotlib图形，无返回值

    Note:
        文件数据格式要求：
        1. 当使用ipath参数时，文件应为空格/制表符分隔的文本文件
        2. 自动处理颜色映射：
            - 颜色数据会自动归一化到[cl, cr]范围
            - cl/cr通过数据集的min/max值自动计算
            - 可通过opt参数中的cmap指定颜色映射
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot
    if pos is None or w is None or c is None:
        if ipath is not None:
            import numpy as np
            d = np.loadtxt(ipath)
            pos = d[:, 0: 4]
            w = d[:, iw]
            c = d[:, ic]

    if clabel is not None or ctitle is not None:
        if cbar is None:
            cbar = {}
        if clabel is not None:
            cbar['label'] = clabel
        if ctitle is not None:
            cbar['title'] = ctitle

    # 执行绘图
    plot(add_axes2, add_fn2, pos=pos, w=w, c=c, w_min=w_min, w_max=w_max,
         cbar=cbar,
         fn2_aspect='equal',
         title=title, xlabel=xlabel, ylabel=ylabel, xlim=xlim, ylim=ylim, **opt
         )


def test():
    from zmlx.plt.data.example_fn2 import pos, w, c
    show_fn2(pos, w, c, w_max=3, clabel='Pressure', ctitle='Pa')


if __name__ == '__main__':
    test()
