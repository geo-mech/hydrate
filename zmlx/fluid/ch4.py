# -*- coding: utf-8 -*-
"""
定义甲烷气体的参数

by 张召彬
"""

import math
import warnings
from zml import Interp2, TherFlowConfig, data_version


def create(tmin=270, tmax=290, pmin=1e6, pmax=40e6):
    """
    参考：http://www.basechem.org/chemical/434

    气相标准热熔(J·mol-1·K-1)：35.69
    分子量	16.04
    比热： 35.69 * 1000 / 16.04 = 2225.062344139651  (J·KG-1·K-1)
    """

    assert 250 < tmin < tmax < 500
    assert 0.01e6 < pmin < pmax < 50e6

    def get_density(P, T):
        T = max(tmin, min(tmax, T))
        P = max(pmin, min(pmax, P))
        return (0.016042 * P / (8.314 * T)) * (1.0 + 0.025 * P / 1.0E6 - 0.000645 * math.pow(P / 1.0E6, 2))

    def get_viscosity(P, T):
        T = max(tmin, min(tmax, T))
        P = max(pmin, min(pmax, P))
        return 10.3E-6 * (1.0 + 0.053 * (P / 1.0E6) * math.pow(280.0 / T, 3))

    def create_density():
        den = Interp2()
        den.create(pmin, 0.1e6, pmax, tmin, 1, tmax, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 0.1e6, pmax, tmin, 1, tmax, get_viscosity)
        return vis

    if data_version.ch4 >= 221024:
        specific_heat = 2225.062344139651
    else:
        # 之前随手写的，错了
        specific_heat = 1000.0
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create_flu()
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.den, [1e6, 20e6], [270, 290])
    except:
        pass
