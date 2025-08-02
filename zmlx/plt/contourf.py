from zmlx.plt.fig2 import contourf
from zmlx.plt.on_axes import contourf as on_axes

__all__ = ['contourf', 'on_axes']


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
            ncols=2, nrows=1, clear=False, xlabel='x', ylabel='y', cbar=dict(label='Test'), caption='MyTest',
            aspect='equal')
        plot(add_axes2, on_axes, x, y, z, title='contourf',
             index=1, **opts
             )
        plot(add_axes2, tricontourf.on_axes, x.flatten(), y.flatten(), z.flatten(), title='Triangle Contourf',
             index=2, **opts
             )

    gui.execute(f, close_after_done=False)


if __name__ == '__main__':
    test()
