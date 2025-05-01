import os

from zml import Interp2, Seepage


def create(name=None, specific_heat=None):
    if specific_heat is None:
        specific_heat = 2157.82  # J/kg K
    return Seepage.FluDef(den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
                          vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    import warnings
    warnings.warn('use function <create> instead', DeprecationWarning, stacklevel=2)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.fig2 import show_field2
    flu = create()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='den.txt')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='vis.txt')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(show_all, close_after_done=False)
