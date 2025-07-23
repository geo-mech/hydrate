import zmlx.alg.sys as warnings

from zmlx.plt.fig2 import contourf

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)

__all__ = ['contourf']


def test():
    from zmlx.plt.on_axes import add_axes2, contourf, tricontourf
    import numpy as np
    from zmlx.ui import plot, gui
    def f():
        x = np.linspace(-5, 5, 30)
        y = np.linspace(-5, 5, 30)
        x, y = np.meshgrid(x, y)
        z = np.sin(np.sqrt(x ** 2 + y ** 2))

        plot(None, caption='MyTest', clear=True) # 清除之前的内容
        opts = dict(ncols=2, nrows=1, clear=False, xlabel='x', ylabel='y', cbar=dict(label='Test'), caption='MyTest')
        plot(add_axes2, contourf, x, y, z, title='Contourf',
             index=1, **opts
             )
        plot(add_axes2, tricontourf, x.flatten(), y.flatten(), z.flatten(), title='Triangle Contourf',
             index=2, **opts
             )
        # plot(None, caption='MyTest', clear=False, fname='contourf.jpg')

    gui.execute(f, close_after_done=False)


if __name__ == '__main__':
    test()
