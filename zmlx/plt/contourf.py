from zmlx.plt.cbar import add_cbar


def add_contourf(ax, *args, cbar=None, **kwargs):
    """
    绘制二维填充等高线图（云图）。
    Args:
        ax: Axes对象，用于绘制二维填充等高线图
        cbar: 颜色条的配置参数，字典形式
        *args: 传递给ax.contourf函数的参数
        **kwargs: 传递给ax.contourf函数的关键字参数
    Returns:
        绘制的填充等高线图对象
    """
    obj = ax.contourf(*args, **kwargs)
    if cbar is not None:
        add_cbar(ax, obj=obj, **cbar)
    return obj


on_axes = add_contourf


def plot_contourf(
        x=None, y=None, z=None,
        levels=20,
        cmap='coolwarm',
        clabel=None,
        **opts):
    """
    绘制二维填充等高线图（云图），支持灵活的参数配置
    Args:
        x : array-like, optional
            坐标数组，形状需与z的维度匹配。若未提供，将自动生成基于z的索引坐标
        y : array-like, optional
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
        **opts :
            传递给底层plot函数的附加参数
    """
    from zmlx.plt.on_figure import add_axes2
    from zmlx.ui import plot

    plot(add_axes2, add_contourf, x, y, z,
         levels=levels, cmap=cmap, antialiased=True,
         cbar=dict(label=clabel), **opts
         )


contourf = plot_contourf


def test():
    from zmlx.plt.on_figure import add_axes2
    from zmlx.plt import tricontourf
    import numpy as np
    from zmlx.ui import plot, gui
    def f():
        x = np.linspace(-5, 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        z = np.sin(np.sqrt(x ** 2 + y ** 2))

        plot(None, caption='MyTest', clear=True)  # 清除之前的内容
        opts = dict(
            ncols=2, nrows=1, clear=False,
            xlabel='x', ylabel='y',
            cbar=dict(label='Test'), caption='MyTest',
            aspect='equal')
        plot(add_axes2, add_contourf, x, y, z,
             title='contourf',
             index=1, **opts
             )
        plot(add_axes2, tricontourf.on_axes,
             x.flatten(), y.flatten(), z.flatten(),
             title='Triangle Contourf',
             index=2, **opts
             )

    gui.execute(f, close_after_done=False)


if __name__ == '__main__':
    test()
