"""
基于Matplotlib的二维绘图
"""

from zmlx.ui.GuiBuffer import gui, plot

version = 221027


def tricontourf(ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None, iz=None,
                triangulation=None, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]
        if iz is not None:
            z = data[:, iz]

    if triangulation is None:
        return ax.tricontourf(x, y, z, levels=levels, cmap=cmap, antialiased=True)
    else:
        return ax.tricontourf(triangulation, z, levels=levels,
                              cmap=cmap, antialiased=True)


kernels = {'tricontourf': tricontourf}


def plot2(data=None, *, title=None,
          xlabel='x', ylabel='y',
          aspect=None, xlim=None, ylim=None,
          **opts):
    """
    调用其它内核函数来做一个二维的绘图. 可以多个数据叠加绘图;
    其中plots为绘图的数据，其中的每一个item都是一个dict，在每一个dict中，必须包含三个元素：name, args和krargs
    注意：
        当gui_only为True的时候，则只有的GUI上面绘图;
        当给定的title的时候，将在图片的顶部显示一个标题.
    """
    def on_figure(fig):
        """
        执行绘图
        """
        ax = fig.subplots()
        if data is None:
            return
        if aspect is not None:
            ax.set_aspect(aspect)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        for d in data:
            name = d.get('name')
            if name is not None:
                try:
                    kernel = None
                    if kernel is None and d.get('use_kernel', True):
                        func = kernels.get(name)
                        if func is not None:
                            def kernel(*args, **kwargs):
                                return func(ax, *args, **kwargs)
                    if kernel is None:
                        kernel = getattr(ax, name, None)
                    if kernel is not None:
                        h = kernel(*d.get('args', []), **d.get('kwargs', {}))
                        if d.get('has_colorbar', False):
                            cbar = fig.colorbar(h, ax=ax)
                            clabel = d.get('clabel')
                            if clabel is not None:
                                cbar.set_label(clabel)
                    else:
                        print(f'Warning: can not found kernel <{name}>')
                except Exception as e:
                    print(f'Error: {e}')
        if xlim is not None:
            ax.set_xlim(xlim)
        if ylim is not None:
            ax.set_ylim(ylim)

    # 在gui界面上绘图
    plot(on_figure, **opts)


def test_1():
    """
    测试
    """
    import matplotlib.tri as mtri
    import numpy as np

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5])
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x)
    d1 = dict(
        name='tricontourf',
          kwargs=dict(triangulation=triang, z=z, levels=30),
          has_colorbar=True)

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5]) + 3
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x) + 3
    d2 = dict(name='tricontourf',
          kwargs=dict(triangulation=triang, z=z, levels=10))

    x = np.linspace(0, 5, 100)
    y = np.sin(x)
    d3 = dict(
        name='plot',
        args=[x, y],
        kwargs=dict(c=(1, 0, 0, 0.5))
    )

    x = np.linspace(0, 5, 100)
    y = np.cos(x)
    d4 = dict(
        name='plot',
        args=[x, y],
        kwargs=dict(c='r', linewidth=0.1)
    )

    plot2(data=[d1, d2, d3, d4], caption=None, gui_only=False,
          title=None, fname=None, dpi=200,
          xlabel='x', ylabel='y', clear=True)


def test_2():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    data = [{'name': 'contourf', 'args': [x, y, z]}]
    plot2(data)


if __name__ == '__main__':
    gui.execute(test_1, close_after_done=False)
