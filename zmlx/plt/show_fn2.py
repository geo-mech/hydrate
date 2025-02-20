"""
定义数据格式 fn2，主要包括4列数据，用于定义裂缝位置，1列数据，用于定义裂缝的宽度，
1列数据，用于定义裂缝的颜色（如压力）
"""

from zml import is_array
from zmlx.plt.get_color import get_color
from zmlx.ui.GuiBuffer import gui, plot


def show_fn2(pos=None, w=None, c=None, w_max=4, ipath=None, iw=4, ic=6, clabel=None,
             **opt):
    """
    显示二维裂缝网络数据。其中：
        pos包含4列，为各个线段的位置
        w为各个线条的宽度（原始数据）
        c为各个线条的颜色（原始数据）
        w_max为画图的时候线条的最大宽度
    """
    if pos is None or w is None or c is None:
        if ipath is not None:
            import numpy as np
            d = np.loadtxt(ipath)
            pos = d[:, 0: 4]
            w = d[:, iw]
            c = d[:, ic]

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
    cmap = opt.pop('cmap', None)  # 这个default不可以省略
    if isinstance(cmap, str) or cmap is None:
        from zmlx.plt.get_cm import get_cm
        cmap = get_cm(cmap)

    def on_figure(fig):
        ax = fig.subplots()
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        for idx in range(count):
            x0, y0, x1, y1 = pos[idx]
            ax.plot([x0, x1],
                    [y0, y1],
                    c=get_color(cmap, cl, cr, get_c(idx)),
                    linewidth=0.1 + get_w(idx) * w_max / max(wr, 1.0e-10))
        # 在中心点画一个小三角形，用以显示颜色
        xc = (xl + xr) / 2
        yc = (yl + yr) / 2
        xw = max(xr - xl, yr - yl)
        yw = xw
        tricontourf = ax.tricontourf([xc, xc + xw / 1e6, xc],
                                     [yc, yc, yc + yw / 1e6],
                                     [cl, (cl + cr) / 2, cr],
                                     levels=20)
        cbar = fig.colorbar(tricontourf, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

        ratio = max(xr - xl, 1.0e-10) / max(yr - yl, 1.0e-10)
        if 0.05 <= ratio <= 20:
            ax.set_aspect('equal')

    # 执行绘图
    plot(on_figure, **opt)


def test():
    from zmlx.data.example_fn2 import pos, w, c
    gui.execute(lambda: show_fn2(pos, w, c),
                close_after_done=False)


if __name__ == '__main__':
    test()
