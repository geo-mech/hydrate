import os
import zmlx.alg.sys as warnings

from zmlx.base.zml import Interp2
from zmlx.config.TherFlowConfig import TherFlowConfig


def create(name=None):
    return TherFlowConfig.FluProperty(
        den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
        vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
        specific_heat=2225.062344139651, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.fig2 import show_field2
    flu = create()
    show_field2(flu.den, [1e6, 30e6], [250, 600], caption='den')
    show_field2(flu.vis, [1e6, 30e6], [250, 600], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(show_all, close_after_done=False)
