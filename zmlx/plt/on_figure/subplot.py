"""
在这个文件中，处理和figure相关的方法
"""


def add_subplot(
        figure, on_axes=None, *args, nrows=1, ncols=1, index=1, projection=None, label=None,
        xlabel=None, ylabel=None, zlabel=None, title=None,
        view_opts=None, aspect=None, xlim=None, ylim=None, zlim=None, show_legend=False,
        grid=None, axis=None, tight_layout=None,
        **kwargs):
    """
    在figure上添加三维坐标轴并且画图. 第一个参数是figure，第二个参数是绘图的回调函数，在Axes上绘图.
    除了明确给定的这些参数之外，其余的args和kwargs都会传递给on_axes内核使用.

    Args:
        tight_layout: 是否调用figure.tight_layout (当此参数为dict的时候，将传递给figure.tight_layout)
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
        aspect: 子图的宽高比
        xlim: x轴的范围；
        ylim: y轴的范围
        zlim: z轴的范围
        show_legend: 是否显示图例
        grid: 网格
        axis: 坐标轴
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
    if aspect:
        ax.set_aspect(aspect)
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    if zlim is not None:
        ax.set_zlim(zlim)
    if show_legend:
        ax.legend()
    if grid is not None:
        ax.grid(grid)
    if axis is not None:
        ax.axis(axis)
    if tight_layout:
        opt = tight_layout if isinstance(tight_layout, dict) else {}
        figure.tight_layout(**opt)
    return ax  # 返回去，方便后续的操作


def add_axes2(*args, **kwargs):
    """
    在figure上添加二维的坐标轴
    """
    return add_subplot(*args, **kwargs)


def add_axes3(*args, **kwargs):
    """
    在figure上添加三维的坐标轴
    """
    return add_subplot(*args, projection='3d', **kwargs)


def plot_on_figure(*args, **kwargs):
    from zmlx.ui import plot
    return plot(*args, **kwargs)
