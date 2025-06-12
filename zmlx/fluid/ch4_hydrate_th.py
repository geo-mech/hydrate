"""
定义甲烷水合物的基本参数
"""

import math

import zmlx.alg.sys as warnings
from zml import Seepage, Interp2


def create(MH, NH=6, t_min=270, t_max=290, p_min=1e6, p_max=40e6, name=None):
    """
    根据Tough+Hydrate 1.5手册的27页公式2.30来计算密度。

    看上去还不对，勿用!!

    甲烷水合物的比热随着温度和压力略有变化，但是变化的幅度很小，所以可以视为常数:
    参考：
    https://pubs.usgs.gov/fs/2007/3041/pdf/FS-2007-3041.pdf

    大约2100左右
    """
    warnings.warn('密度的数值看上去还不对', RuntimeWarning)
    a1 = 3.38496e-4
    a2 = 5.40099e-7
    a3 = -4.76946e-11
    a4 = 1.0e-10
    T0 = 298.15
    P0 = 1.0e5
    v0 = 1000.0 * MH / (22.712 * NH)

    def get_density(P, T):
        dP = max(p_min, min(p_max, P)) - P0
        dT = max(t_min, min(t_max, T)) - T0
        return 1.0 / (v0 * math.exp(
            a1 * dT + a2 * dT ** 2 + a3 * dT ** 3 + a4 * dP))

    def create_density():
        den = Interp2()
        den.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_density)
        return den

    return Seepage.FluDef(
        den=create_density(),
        vis=1.0e30,
        specific_heat=2100.0, name=name)


if __name__ == '__main__':
    flu = create(100)
    print(flu)
    try:
        from zmlx.plt.fig2 import show_field2

        show_field2(flu.den, [1e6, 20e6], [270, 290])
    except:
        pass
