"""
定义甲烷气体的参数

by 张召彬
"""

import math
import warnings

from zml import Interp2, Seepage, data_version


def create(t_min=270, t_max=290, p_min=1e6, p_max=40e6, name=None):
    """
    参考：http://www.basechem.org/chemical/434

    气相标准热熔(J·mol-1·K-1)：35.69
    分子量	16.04
    比热： 35.69 * 1000 / 16.04 = 2225.062344139651  (J·KG-1·K-1)
    """

    assert 250 < t_min < t_max < 500
    assert 0.01e6 < p_min < p_max < 50e6

    def get_density(P, T):
        T = max(t_min, min(t_max, T))
        P = max(p_min, min(p_max, P))
        return (0.016042 * P / (8.314 * T)) * (1.0 + 0.025 * P / 1.0E6 - 0.000645 * math.pow(P / 1.0E6, 2))

    def get_viscosity(P, T):
        T = max(t_min, min(t_max, T))
        P = max(p_min, min(p_max, P))
        return 10.3E-6 * (1.0 + 0.053 * (P / 1.0E6) * math.pow(280.0 / T, 3))

    def create_density():
        den = Interp2()
        den.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_viscosity)
        return vis

    if data_version.ch4 >= 221024:
        specific_heat = 2225.062344139651
    else:
        # 之前随手写的，错了
        specific_heat = 1000.0
    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.show_field2 import show_field2
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(show_all, close_after_done=False)
