from zmlx.plt.plot_on_figure import plot_on_figure


def plot_on_axes(on_axes, dim=2, xlabel=None, ylabel=None, zlabel=None,
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


if __name__ == '__main__':
    test_1()
