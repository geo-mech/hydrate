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

