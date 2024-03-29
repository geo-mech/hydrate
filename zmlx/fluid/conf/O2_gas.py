# -*- coding: utf-8 -*-
"""

@author: Maryelin

Specific Heat of Oxigen Gas  from:
https://www.engineeringtoolbox.com/oxygen-d_978.html
"""
from zmlx.fluid.conf.gas_density.O2_density import *
from zmlx.fluid.conf.gas_viscosity.O2_viscosity import *
from zml import Interp2, TherFlowConfig, data_version

def create_flu(tmin=280, tmax=700, pmin=1.0e6, pmax=20.0e6):
    
    assert 250 < tmin < tmax < 750
    assert 0.01e6 < pmin < pmax < 30.0e6
    
    def liq_den(P, T):
        density = den_O2(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 280, 10, 750, get_density)
        return den

    def liq_vis(P, T):
        viscosity = vis_o2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1090  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


if __name__ == '__main__':
    flu = create_flu()
