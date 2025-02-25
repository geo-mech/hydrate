"""
基于Matplotlib的二维绘图
"""

from zmlx.plt.plot_on_axes import plot_on_axes

version = 250401


def tricontourf(ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None,
                iz=None,
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
        return ax.tricontourf(x, y, z, levels=levels, cmap=cmap,
                              antialiased=True)
    else:
        return ax.tricontourf(triangulation, z, levels=levels,
                              cmap=cmap, antialiased=True)


kernels = {'tricontourf': tricontourf}


def plot2(data=None, **opts):
    """
    调用内核函数来做一个二维的绘图. 可以多个数据叠加绘图;
    其中plots为绘图的数据，其中的每一个item都是一个dict，
        在每一个dict中，必须包含三个元素：name, args和kwargs
    """

    def on_axes(ax):
        """
        执行绘图
        """
        if data is None:
            return
        for d in data:
            name = d.get('name')
            if name is None:
                continue
            args, kwargs, kwds = d.get('args', []), d.get(
                'kwargs', {}), d.get('kwds', {})
            kwargs.update(kwds)  # 优先使用kwds
            succeed = False
            obj = None
            if not succeed:
                try:  # 优先去使用标准的版本
                    obj = getattr(ax, name, None)(*args, **kwargs)
                    succeed = True
                except:
                    pass
            if not succeed:
                try:  # 尝试使用自定义的内核函数
                    obj = kernels.get(name)(ax, *args, **kwargs)
                    succeed = True
                except:
                    pass
            if succeed:  # 绘图成功，尝试添加colorbar
                clabel = d.get('clabel')
                if d.get('has_colorbar') or clabel is not None:
                    cbar = ax.get_figure().colorbar(obj, ax=ax)
                    if clabel is not None:
                        cbar.set_label(clabel)
            else:
                print(f'plot failed: name={name}, '
                      f'args={args}, kwargs={kwargs}')

    plot_on_axes(on_axes, dim=2, **opts)


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
        kwds=dict(triangulation=triang, z=z, levels=30),
        has_colorbar=True)

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5]) + 3
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x) + 3
    d2 = dict(
        name='tricontourf',
        kwds=dict(triangulation=triang, z=z, levels=10))

    x = np.linspace(0, 5, 100)
    y = np.sin(x)
    d3 = dict(
        name='plot',
        args=[x, y],
        kwds=dict(c=(1, 0, 0, 0.5))
    )

    x = np.linspace(0, 5, 100)
    y = np.cos(x)
    d4 = dict(
        name='plot',
        args=[x, y],
        kwds=dict(c='r', linewidth=0.1)
    )

    plot2(data=[d1, d2, d3, d4], xlabel='x', ylabel='y')


if __name__ == '__main__':
    test_1()
