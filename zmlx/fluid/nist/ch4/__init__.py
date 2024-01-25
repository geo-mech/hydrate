import os

import numpy as np
from scipy.interpolate import LinearNDInterpolator

from zml import Interp2, Seepage
from zmlx.filesys.join_paths import join_paths


def create(t_min=261, t_max=329, p_min=2.0e6, p_max=99.0e6, name=None):
    """
    创建液态co2的定义.
    """
    data = np.loadtxt(fname=join_paths(os.path.dirname(__file__), 'CO2.txt'))
    den = LinearNDInterpolator(data[:, 0: 2], data[:, 2], rescale=True, fill_value=np.nan)
    vis = LinearNDInterpolator(data[:, 0: 2], data[:, 3], rescale=True, fill_value=np.nan)

    def gas_den(P, T):
        assert 260 <= T <= 330
        assert 1e6 <= P <= 100E6
        return den(T, P)

    def gas_vis(P, T):
        assert 260 <= T <= 330
        assert 1e6 <= P <= 100E6
        return vis(T, P)

    def create_density():
        den = Interp2()
        den.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_den)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_vis)
        return vis

    specific_heat = 2225.062

    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat,
                          name=name)


def test():
    t_min = 274
    t_max = 294
    p_min = 10.0e6
    p_max = 30.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max)
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2
        show_field2(flu.den, [p_min, p_max], [t_min, t_max], caption='density')
        show_field2(flu.vis, [p_min, p_max], [t_min, t_max], caption='viscosity')
    except:
        pass


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test, close_after_done=False)
