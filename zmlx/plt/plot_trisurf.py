from zmlx.ui.GuiBuffer import plot


def plot_trisurf(x=None, y=None, z=None,
                 title=None,
                 cmap='coolwarm',
                 xlabel=None,
                 ylabel=None,
                 zlabel=None,
                 **opts):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置

    Parameters
    ----------
    x, y, z : array-like, 1D
        数据点的三维坐标数组，必须为相同长度的一维数组
    title : str, optional
        图标题，默认不显示
    cmap : str or Colormap, default 'coolwarm'
        曲面颜色映射，支持所有Matplotlib注册的colormap名称
    xlabel, ylabel, zlabel : str, optional
        坐标轴标签，默认不显示
    **opts : dict
        传递给底层plot3函数的附加参数
    """

    def on_figure(fig):
        ax = fig.add_subplot(111, projection='3d')

        # 坐标轴标签配置
        if xlabel is not None:
            ax.set_xlabel(xlabel)

        if ylabel is not None:
            ax.set_ylabel(ylabel)

        if zlabel is not None:
            ax.set_zlabel(zlabel)

        if title is not None:
            ax.set_title(title)

        res = ax.plot_trisurf(x, y, z, cmap=cmap, antialiased=True)
        fig.colorbar(res, ax=ax)

    plot(on_figure, **opts)


def test_1():
    import numpy as np
    # 生成 x 和 y 坐标
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)

    # 生成网格
    X, Y = np.meshgrid(x, y)

    # 生成 z 坐标
    Z = np.sin(np.sqrt(X ** 2 + Y ** 2))
    plot_trisurf(x=X.flatten(), y=Y.flatten(), z=Z.flatten())


if __name__ == '__main__':
    from zmlx.ui.GuiBuffer import gui

    gui.execute(test_1, close_after_done=False)
