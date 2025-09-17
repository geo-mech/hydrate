import zmlx.alg.sys as warnings

from zmlx.plt.fn2 import show_fn2

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.plt.data.example_fn2 import pos, w, c
    show_fn2(pos, w, c, w_max=3, clabel='Pressure [Pa]', gui_mode=True)


if __name__ == '__main__':
    test()
