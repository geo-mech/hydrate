from zmlx.plt.on_axes.cbar import add_cbar


def add_surf(ax, x, y, z, c, *, alpha=None, clim=None, cmap=None, cbar=None,
             edgecolor=None):
    """
    添加一个曲面
    Args:
        ax: 目标Axes对象
        x: x坐标矩阵 (二维的矩阵)
        y: y坐标矩阵 (二维的矩阵)
        z: z坐标矩阵 (二维的矩阵)
        c: 用于颜色映射的数值矩阵 （二维的矩阵）。 注意: x, y, z, v 应该具有同样的大小
        alpha: 透明度，默认None表示不透明
        clim: 数值范围，默认None表示自动计算
        cmap: 颜色映射，默认None表示使用viridis
        cbar: 颜色条参数，默认None表示不添加
        edgecolor: 边缘颜色，默认None表示不添加

    Returns:
        曲面对象
    """
    import matplotlib.pyplot as plt
    import matplotlib

    if clim is None:
        clim = c.min(), c.max()

    norm = plt.Normalize(vmin=clim[0], vmax=clim[1])

    if cmap is None:
        cmap = 'viridis'

    if isinstance(cmap, str):
        from zmlx.plt.cmap import get_cm
        cmap = get_cm(cmap)

    assert isinstance(cmap, matplotlib.colors.Colormap)

    # 计算颜色
    colors = cmap(norm(c))

    # 设置透明度
    if alpha is not None:
        alpha[alpha < 0] = 0
        alpha[alpha > 1] = 1
        colors[..., -1] = alpha

    # 绘制曲面
    surf = ax.plot_surface(
        x, y, z,
        facecolors=colors,  # 使用V值决定颜色
        shade=False,  # 关闭默认着色（使用自定义颜色）
        rstride=1,  # 行方向步长
        cstride=1,  # 列方向步长
        antialiased=False
    )

    # 添加颜色条
    if cbar is not None:
        add_cbar(ax, clim=clim, cmap=cmap, **cbar)

    # 设置平滑着色
    if edgecolor is None:
        edgecolor = 'none'
    surf.set_edgecolor(edgecolor)  # 隐藏网格线

    # 返回曲面对象
    return surf
