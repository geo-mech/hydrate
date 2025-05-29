import zmlx.alg.sys as warnings

from zmlx.plt.fig3 import show_rc3

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
              DeprecationWarning, stacklevel=2)


def test():
    from zmlx.geometry.dfn_v3 import to_rc3, create_demo
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(5, 9))
        alpha.append(random.uniform(0, 1))
    show_rc3(rc3, gui_mode=True)


if __name__ == '__main__':
    test()
