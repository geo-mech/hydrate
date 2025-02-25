from zmlx.plt.plot_on_axes import plot_on_axes


def plot_trisurf(x=None, y=None, z=None,
                 cmap='coolwarm',
                 **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置

    Parameters
    ----------
    x, y, z : array-like, 1D
        数据点的三维坐标数组，必须为相同长度的一维数组
    cmap : str or Colormap, default 'coolwarm'
        曲面颜色映射，支持所有Matplotlib注册的colormap名称
    **kwargs : dict
        传递给底层plot_on_axes函数的附加参数
    """

    def on_axes(ax):
        res = ax.plot_trisurf(x, y, z, cmap=cmap, antialiased=True)
        ax.get_figure().colorbar(res, ax=ax)

    plot_on_axes(on_axes, dim=3, **kwargs)


def test_1():
    import numpy as np
    # 生成 x 和 y 坐标
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)

    # 生成网格
    X, Y = np.meshgrid(x, y)

    # 生成 z 坐标
    Z = np.sin(np.sqrt(X ** 2 + Y ** 2))
    plot_trisurf(x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
                 gui_mode=True)


if __name__ == '__main__':
    test_1()
