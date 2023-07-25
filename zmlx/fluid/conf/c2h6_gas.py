"""
Created on Mon Jun  5 16:09:29 2023

@author: Maryelin
"""
from zml import Interp2, TherFlowConfig
from zmlx.fluid.conf.gas_density.c2h6 import den_c2h6
from zmlx.fluid.conf.gas_viscosity.c2h6 import gas_vis_c2h6


def create_flu(tmin=280, tmax=1000, pmin=1.0e6, pmax=40.0e6):
    assert 250 < tmin < tmax < 1500
    assert 0.01e6 < pmin < pmax < 50.0e6

    def gas_den(P, T):
        density = den_c2h6(P, T)
        return density

    def get_density(P, T):
        return gas_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_c2h6(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1385.43  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


if __name__ == '__main__':
    flu = create_flu()
