"""
在这里，定义在Axes绘图的操作. 这些绘图，将是绘图的基础.
"""
from zmlx.plt.on_figure import plot_on_figure


def add_subplot(
        figure, on_axes, *args, nrows=1, ncols=1, index=1, projection=None, label=None,
        xlabel=None, ylabel=None, zlabel=None, title=None,
        view_opts=None,
        **kwargs):
    """
    在figure上添加三维坐标轴并且画图. 第一个参数是figure，第二个参数是绘图的回调函数，在Axes上绘图.
    除了明确给定的这些参数之外，其余的args和kwargs都会传递给on_axes内核使用.

    Args:
        figure: 图形的Figure实例
        on_axes: 在Axes上绘图的回调函数，函数的原型为:
            def on_axes(ax):
                ...
                其中ax为matplotlib的Axes实例
        nrows: 子图的行数
        ncols: 子图的列数
        label: 子图的标签 (如果给定，则会优先使用已经存在的Axes，从而使得在同一个Axes上可以绘制多个图形)
        index (int|tuple): 子图的索引
        projection: 子图的投影类型，如'3d'
        xlabel: x轴的标签
        ylabel: y轴的标签
        zlabel: z轴的标签
        title: 图表的标题(当前的Axes上的)
        view_opts: 视角设置，字典形式，如{'elev': 35, 'azim': -120}
        *args: 传递给on_axes函数的参数
        **kwargs: 传递给on_axes函数的关键字参数
    """
    ax = None
    if label is not None:  # 给定了label，则优先去找到已经存在的Axes
        for item in figure.axes:
            if item.get_label() == label:
                ax = item
                break
    if ax is None:
        ax = figure.add_subplot(nrows, ncols, index, projection=projection, label=label)
    try:
        if callable(on_axes):
            on_axes(ax, *args, **kwargs)
    except Exception as err:
        print(err)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if zlabel:
        ax.set_zlabel(zlabel)
    if title:
        ax.set_title(title)
    if view_opts:  # elev=35, azim=-120
        ax.view_init(**view_opts)
    return ax  # 返回去，方便后续的操作


def add_axes2(*args, **kwargs):
    return add_subplot(*args, **kwargs)


def add_axes3(*args, **kwargs):
    return add_subplot(*args, projection='3d', **kwargs)


def scatter3(
        ax, x, y, z, c=None, alpha=1.0,
        clabel=None,
        cmap=None):
    """
    在给定Axes上绘制散点图.

    Args:
        ax: Axes对象，用于绘制散点图
        x: 数据点的x坐标数组
        y: 数据点的y坐标数组
        z: 数据点的z坐标数组
        c: 数据点的颜色值数组
        alpha: 数据点的透明度
        clabel: 颜色条的标签
        cmap: 颜色映射
    """
    if c is None:
        c = z
    if cmap is None:
        cmap = 'coolwarm'
    obj = ax.scatter(x, y, z, c=c, cmap=cmap, alpha=alpha)
    ax.get_figure().colorbar(obj, ax=ax, shrink=0.6, aspect=10, label=clabel)
    return obj


def contourf(ax, *args, cbar=None, **kwargs):
    """
    绘制二维填充等高线图（云图），支持灵活的参数配置
    """
    kwargs.setdefault('antialiased', True)
    obj = ax.contourf(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


def tricontourf(ax, *args, cbar=None, **kwargs):
    """
    绘制二维填充等高线图（云图），支持灵活的参数配置
    """
    kwargs.setdefault('antialiased', True)
    obj = ax.tricontourf(*args, **kwargs)
    if cbar is not None:
        ax.get_figure().colorbar(obj, ax=ax, **cbar)
    return obj


def call_ax(ax, name, *args, **kwargs):
    """
    调用Axes的方法
    """
    return getattr(ax, name)(*args, **kwargs)


def curve2(ax, *args, **kwargs):
    """
    绘制二维曲线图. 从x到y的曲线
    """
    return ax.plot(*args, **kwargs)


def curve3(ax, *args, **kwargs):
    """
    绘制3维曲线图
    """
    return ax.plot(*args, **kwargs)


def plot_on_axes(
        on_axes, dim=2, xlabel=None, ylabel=None, zlabel=None,
        title=None, aspect=None,
        xlim=None, ylim=None, zlim=None,
        show_legend=False, grid=None, axis=None,
        **opts):
    """
    绘制图形。使用在坐标轴上绘图的回调函数.

    Args:
        on_axes: 在坐标轴上ax上绘图的回调函数，函数的原型为:
            def on_axes(ax):
                ...
                其中ax为matplotlib的axes实例，会根据dim的取值而创建并传递给on_axes。
        dim: 维度，2或者3 (创建的Axes的类型会不同)
        xlabel: x轴标签，当非None的时候，会设置axes.set_xlabel(xlabel) (默认为None)
        ylabel: y轴标签，当非None的时候，会设置axes.set_ylabel(ylabel) (默认为None)
        zlabel: z轴标签，当非None的时候，会设置axes.set_zlabel(zlabel) (默认为None)
        title: 标题，当非None的时候，会设置axes.set_title(title) (默认为None)
        aspect: 坐标的比例，当非None的时候，会设置axes.set_aspect(aspect) (默认为None)
        zlim: z轴的范围，当非None的时候，会设置axes.set_zlim(zlim) (默认为None)
        ylim: y轴的范围，当非None的时候，会设置axes.set_ylim(ylim) (默认为None)
        xlim: x轴的范围，当非None的时候，会设置axes.set_xlim(xlim) (默认为None)
        axis: 设置axis
        grid: 是否显示网格线
        show_legend: 是否显示图例
        opts: 传递给底层plot函数的附加参数，主要包括：
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)
            fname (str|None): 保存的文件名，默认为None (即仅仅绘图，不保存文件)
            dpi (int): 保存的图片的分辨率 (默认为300)
            gui_mode (bool): 是否强制在zml的界面上绘图(即如果界面不存在，则自动自动一个界面)
    Returns:
        None
    """

    def on_figure(fig):
        assert dim == 2 or dim == 3, f'The dim must be 2 or 3 while got {dim}'
        if dim == 2:
            ax = fig.subplots()
        else:
            ax = fig.add_subplot(111, projection='3d')
        try:
            on_axes(ax)
        except Exception as e:
            print(e)

        if xlabel is not None:
            ax.set_xlabel(xlabel)
        if ylabel is not None:
            ax.set_ylabel(ylabel)
        if zlabel is not None and dim == 3:
            ax.set_zlabel(zlabel)
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)
        if zlim is not None and dim == 3:
            ax.set_zlim(zlim)
        if title is not None:
            ax.set_title(title)
        if aspect is not None:
            ax.set_aspect(aspect)
        if show_legend:
            ax.legend()
        if grid is not None:
            ax.grid(grid)
        if axis is not None:
            ax.axis(axis)

    plot_on_figure(on_figure, **opts)


def test_1():
    def on_axes(ax):
        ax.plot([1, 2, 3], [4, 5, 6])

    plot_on_axes(on_axes, xlabel='x', ylabel='y',
                 title='title', caption='caption', gui_mode=True)


def test_2():
    from zmlx import plot

    def on_figure(figure):
        add_subplot(
            figure, curve2, [1, 2, 3], [1, 4, 9],
            title='线性图',
            nrows=2, ncols=3, index=1, label='xy')
        add_subplot(
            figure, curve2, [1, 2, 3], [2, 5, 7],
            title='线性图',
            nrows=2, ncols=3, index=1, label='xy')
        add_subplot(
            figure,
            call_ax, 'scatter', [1, 2, 3], [3, 2, 1],
            title='散点图',
            color='red',
            nrows=2, ncols=3, index=2)
        add_subplot(
            figure, None,
            title='极坐标图',
            projection='polar',
            nrows=2, ncols=3, index=3)
        add_subplot(
            figure, call_ax, 'bar', ['A', 'B', 'C'], [3, 7, 2],
            title='条形图',
            nrows=2, ncols=3, index=(4, 6)
        )

    plot(on_figure, gui_mode=True)


def test_3():
    import numpy as np
    from zmlx import plot, gui
    def f():
        opts = dict(nrows=2, ncols=3, clear=False, caption='我的绘图测试')
        opts_xy = dict(title='线性图', index=1, label='xy', **opts)
        plot(add_subplot, curve2, [1, 2, 3], [1, 4, 9],
             **opts_xy
             )
        plot(add_subplot, curve2, [1, 2, 3], [2, 5, 7],
             **opts_xy
             )
        plot(add_subplot,
             call_ax, 'scatter', [1, 2, 3], [3, 2, 1],
             title='散点图',
             color='red',
             index=2, **opts)
        plot(add_subplot, None,
             title='极坐标图',
             projection='polar',
             index=3, **opts)
        plot(add_subplot, call_ax, 'bar', ['A', 'B', 'C'], [3, 7, 2],
             title='条形图',
             index=(4, 5), **opts)
        x = np.random.rand(100)
        y = np.random.rand(100)
        z = np.random.rand(100)
        c = np.random.rand(100)
        plot(add_subplot, scatter3, x, y, z, c,
             title='My Scatter',
             index=6,
             xlabel='x/m', projection='3d', **opts)

    gui.execute(f, close_after_done=False)


def test_4():
    import numpy as np
    from zmlx import plot, gui
    z = np.linspace(0, -10, 100)
    y = np.sin(z)
    x = np.cos(z)
    plot(add_axes3, curve3, x, y, z,
         xlabel='x', ylabel='y', zlabel='z',
         gui_mode=True
         )

if __name__ == '__main__':
    test_3()
