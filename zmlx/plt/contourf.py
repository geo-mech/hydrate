from zmlx.plt.plot_on_axes import plot_on_axes


def contourf(x=None, y=None, z=None,
             levels=20,
             cmap='coolwarm',
             clabel=None,
             **opts):
    """
    绘制二维填充等高线图（云图），支持灵活的参数配置

    Parameters
    ----------
    x, y : array-like, optional
        坐标数组，形状需与z的维度匹配。若未提供，将自动生成基于z的索引坐标
    z : array-like,2D
        二维标量数据数组，形状为 (ny, nx)
    levels : int or array-like, default 20
        等高线层级配置：
        - 整数：自动生成该数量的等间距层级
        - 数组：使用指定值作为层级边界
    cmap : str or Colormap, default 'coolwarm'
        颜色映射名称或Colormap对象
    clabel : str, optional
        是否显示等高线标签，默认由绘图后端决定
    **opts : dict
        传递给底层plot函数的附加参数
    """

    def on_axes(ax):
        item = ax.contourf(
            x, y, z,
            levels=levels, cmap=cmap, antialiased=True
        )
        cbar = ax.get_figure().colorbar(item, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    plot_on_axes(on_axes, **opts)


def test():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    contourf(x, y, z)


if __name__ == '__main__':
    test()
