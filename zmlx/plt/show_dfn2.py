import zmlx.alg.sys as warnings

from zmlx.plt.fig2 import show_dfn2

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def __test():
    from zmlx.geometry.dfn2 import dfn2
    fractures = dfn2(lr=[10, 100], ar=[0, 1], p21=0.2, xr=[-100, 100],
                     yr=[-100, 100], l_min=2)
    show_dfn2(fractures)


if __name__ == '__main__':
    __test()
