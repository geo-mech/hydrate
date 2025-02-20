"""
基于Matplotlib的三维绘图
"""

from zmlx.plt.plot import plot


def plot3(*args, **kwargs):
    """
    调用内核函数来做一个三维绘图. 可以多个数据叠加绘图
    """
    kwargs.update(dict(dim=3))
    return plot(*args, **kwargs)


def test_1():
    import numpy as np
    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    data = [
        dict(
            name='plot_trisurf',
            args=[x.flatten(), y.flatten(), z.flatten()],
            kwargs=dict(cmap='coolwarm', antialiased=True)
        )
    ]
    plot3(data)


if __name__ == '__main__':
    from zmlx.ui import gui
    gui.execute(test_1, close_after_done=False)
