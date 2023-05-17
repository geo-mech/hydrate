# -*- coding: utf-8 -*-


from zml import Interp2, TherFlowConfig
import os


def create_flu():
    return TherFlowConfig.FluProperty(den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
                                      vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
                                      specific_heat=2225.062344139651)


def show_all():
    from zmlx.plot.show_field2 import show_field2
    flu = create_flu()
    show_field2(flu.den, [1e6, 20e6], [280, 300], caption='den')
    show_field2(flu.vis, [1e6, 20e6], [280, 300], caption='vis')


if __name__ == '__main__':
    from zml import gui
    gui.execute(show_all, close_after_done=False)

