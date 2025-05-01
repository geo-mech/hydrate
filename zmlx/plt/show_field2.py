import warnings

from zmlx.plt.fig2 import show_field2

warnings.warn(f'The modulus {__name__} is deprecated and '
              f'will be removed after 2026-4-16',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


def test_1():
    from zmlx.fluid.ch4 import create
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test_1, close_after_done=False)
