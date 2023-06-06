# -*- coding: utf-8 -*-
"""

@author: Maryelin
"""

from zmlx.fluid.conf.liqu_density.c2h6 import liq_den_c2h6
from zmlx.fluid.conf.liqu_viscosity.c2h6 import liq_vis_c2h6
from zml import Interp2, TherFlowConfig, data_version


def create_flu(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    
    
    def liq_den(P, T):
        density = liq_den_c2h6(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 20, 10, 280, get_density)
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