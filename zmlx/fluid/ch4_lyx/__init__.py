# -*- coding: utf-8 -*-


from zml import Interp2, TherFlowConfig
import os
import warnings


def create():
    return TherFlowConfig.FluProperty(den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
                                      vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
                                      specific_heat=2225.062344139651)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.show_field2 import show_field2
    flu = create_flu()
    show_field2(flu.den, [1e6, 30e6], [250, 600], caption='den')
    show_field2(flu.vis, [1e6, 30e6], [250, 600], caption='vis')


if __name__ == '__main__':
    from zml import gui

    gui.execute(show_all, close_after_done=False)
