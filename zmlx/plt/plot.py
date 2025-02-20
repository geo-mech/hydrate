"""
基于Matplotlib的二维绘图
"""

from zmlx.ui.GuiBuffer import plot as do_plot


def parse(value, space: dict):
    """
    从变量空间中读取数值
    """
    if isinstance(value, str):
        return space.get(value, value)
    elif isinstance(value, (list, tuple)):
        processed = [parse(item, space) for item in value]
        return type(value)(processed)
    elif isinstance(value, dict):
        return {k: parse(v, space) for k, v in value.items()}
    else:
        return value


def plot(data=None, dim=2, create_ax=None, **opts):
    """
    执行绘图. 可以多个数据叠加绘图;
    """
    def on_figure(fig, cmds):
        """
        执行绘图
        """
        if cmds is None:
            return
        space = {'fig': fig}
        ax = None
        if create_ax is not None:
            ax = create_ax(fig)
        if ax is None:
            assert dim == 2 or dim == 3
            if dim == 2:
                ax = fig.subplots()
            elif dim == 3:
                ax = fig.add_subplot(111, projection='3d')
        if ax is None:
            return
        space['ax'] = ax  # 绘图的坐标轴
        for cmd in cmds:
            if not isinstance(cmd, dict):
                continue
            obj = cmd.get('obj')
            if isinstance(obj, str):
                obj = space.get(obj)
            if obj is None:
                obj = ax
            func = cmd.get('func')
            if func is None:
                func = cmd.get('name')
            if not isinstance(func, str):
                continue
            func = getattr(obj, func, None)
            if func is None:
                continue
            args = cmd.get('args', [])
            kwds = cmd.get('kwds', {})
            kwds.update(cmd.get('kwargs', {}))
            try:
                result = func(*parse(args, space), **parse(kwds, space))
            except Exception as e:
                print(f'Error: {e}')
                continue
            res = cmd.get('res', 'res')  # 默认为res
            if isinstance(res, str):
                space[res] = result
    do_plot(kernel=lambda fig: on_figure(fig, cmds=data), **opts)


def test_1():
    """
    测试
    """
    import matplotlib.tri as mtri
    import numpy as np

    x = np.linspace(0, 5, 100)
    y = np.sin(x)
    d1 = dict(
        name='plot',
        args=[x, y],
        kwargs=dict(c=(1, 0, 0, 0.5))
    )

    x = np.linspace(0, 5, 100)
    y = np.cos(x)
    d2 = dict(
        name='plot',
        args=[x, y],
        kwargs=dict(c='r', linewidth=0.1)
    )

    x = np.asarray([0, 1, 0, 3, 0.5, 1.5, 2.5, 1, 2, 1.5]) + 3
    y = np.asarray([0, 0, 0, 0, 1.0, 1.0, 1.0, 2, 2, 3.0])
    triangles = [[0, 1, 4], [1, 5, 4], [2, 6, 5],
                 [4, 5, 7], [5, 6, 8], [5, 8, 7],
                 [7, 8, 9], [1, 2, 5], [2, 3, 6]]
    triang = mtri.Triangulation(x, y, triangles)
    z = np.cos(2.5 * x * x) + np.sin(2.5 * x * x) + 3

    d3 = dict(
        name='tricontourf',
        args=[triang, z],
        kwds=dict(levels=30, antialiased=True)
    )

    d4 = dict(
        obj='fig',
        name='colorbar',
        args=['res'],
        kwargs=dict(ax='ax')
    )

    d5 = dict(
        obj='res',
        name='set_label',
        args=['test']
    )

    plot(data=[d1, d2, d3, d4, d5])


if __name__ == '__main__':
    from zmlx.ui import gui
    gui.execute(test_1, close_after_done=False)

