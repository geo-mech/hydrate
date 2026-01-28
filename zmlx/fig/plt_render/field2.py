from zmlx.plt.on_axes.tricontourf import add_tricontourf


def add_field2(ax, f, xr, yr, *, cmap=None, levels=None, clabel=None, cbar=None,
               x_times=1.0, y_times=1.0, z_times=1.0):
    """
    显示一个二维的场，用于测试。注意此函数有很大的效率优化空间。
    Args:
        ax: 用于显示的轴
        f: 一个函数，用于计算z值
        xr: x的范围
        yr: y的范围
        cmap: 颜色映射
        levels: 颜色等级
        clabel: 颜色标签
        cbar: 颜色条选项
        x_times: x轴缩放因子
        y_times: y轴缩放因子
        z_times: z轴缩放因子
    """
    va = [xr[0] + (xr[1] - xr[0]) * i * 0.01 for i in range(101)]
    vb = [yr[0] + (yr[1] - yr[0]) * i * 0.01 for i in range(101)]
    x = []
    y = []
    z = []
    for a in va:
        for b in vb:
            x.append(a * x_times)
            y.append(b * y_times)
            z.append(f(a, b) * z_times)

    if clabel is not None:
        if cbar is None:
            cbar = dict(label=clabel)
        else:
            cbar['label'] = clabel

    return add_tricontourf(
        ax, x, y, z,
        levels=levels,
        cmap=cmap, cbar=cbar
    )
