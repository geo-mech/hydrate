from zmlx.plt.cmap import get_cm


def add_cbar(ax=None, *, title=None, cmap=None, clim=None, fig=None,
             obj=None, **opts):
    """
    在ax上添加一个颜色条，并设置标题、颜色映射、数值范围等
    Args:
        ax: 目标Axes对象
        title: 颜色条标题（显示在颜色条的顶部）
        cmap: 颜色映射 （默认值为'viridis'）
        clim: 数值范围 （默认值为None）
        fig: 目标Figure对象 （默认值为None）
        obj: 颜色映射对象 （默认值为None）
        **opts: 其他参数 (传递给fig.colorbar的参数)

    Returns:
        颜色条对象
    """
    if cmap is None:
        cmap = 'viridis'

    if isinstance(cmap, str):
        cmap = get_cm(cmap)

    if obj is None:
        from matplotlib import cm
        obj = cm.ScalarMappable(cmap=cmap)
        if clim is not None:
            obj.set_clim(clim)
    else:
        assert clim is None, 'clim must be None when obj is not None'

    if fig is None:
        fig = ax.get_figure()

    opts.setdefault('shrink', 0.8)

    bar = fig.colorbar(
        obj, ax=ax, **opts
    )
    if title is not None:
        bar.ax.set_title(title)

    return bar
