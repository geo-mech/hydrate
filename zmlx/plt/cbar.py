from matplotlib import cm


def add_cbar(ax=None, *, label=None, cmap=None, clim=None, fig=None,
             shrink=None, **opts):
    """
    在ax上添加一个颜色条
    Args:
        ax: 目标Axes对象
        label: 颜色条标签
        cmap: 颜色映射
        clim: 数值范围
        fig: 目标Figure对象
        shrink: 颜色条的大小
        **opts: 其他参数

    Returns:
        颜色条对象
    """
    if cmap is None:
        cmap = cm.viridis

    if isinstance(cmap, str):
        from zmlx.plt.cmap import get_cm
        cmap = get_cm(cmap)

    mappable = cm.ScalarMappable(cmap=cmap)
    if clim is not None:
        mappable.set_clim(clim)

    if fig is None:
        fig = ax.get_figure()

    if shrink is None:
        shrink = 0.8

    bar = fig.colorbar(mappable, ax=ax, label=label,
                       shrink=shrink, **opts)
    return bar

