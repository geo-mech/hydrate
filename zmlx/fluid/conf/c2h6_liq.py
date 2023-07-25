"""

@author: Maryelin
"""

from zml import Interp2, TherFlowConfig
from zmlx.fluid.conf.liqu_density.c2h6 import liq_den_c2h6
from zmlx.fluid.conf.liqu_viscosity.c2h6 import liq_vis_c2h6


def create_flu(tmin=200, tmax=280, pmin=1.0e6, pmax=20.0e6):
    assert 150 < tmin < tmax < 260
    assert 0.01e6 < pmin < pmax < 30.0e6

    def liq_den(P, T):
        density = liq_den_c2h6(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 20, 10, tmax, get_density)
        return den

    def liq_vis(P, T):
        viscosity = liq_vis_c2h6(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 2276.02  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


if __name__ == '__main__':
    flu = create_flu()
