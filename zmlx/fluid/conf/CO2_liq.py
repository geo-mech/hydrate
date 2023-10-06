"""

@author: Maryelin
"""


from zmlx.fluid.conf.liqu_density.co2 import liq_den_co2
from zmlx.fluid.conf.liqu_viscosity.co2 import liq_vis_co2
from zml import Interp2, TherFlowConfig, data_version

def create_flu(tmin=100, tmax=250, pmin=1.0e6, pmax=20.0e6):
    
    assert 99 < tmin < tmax < 260
    assert 0.01e6 < pmin < pmax < 30.0e6
    
    def gas_den(P, T):
        density = liq_den_co2(P, T)
        return density
    def get_density(P, T):
        return gas_den(P, T)
    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den  
    
    def gas_vis(P, T):
        viscosity = liq_vis_co2(P, T)
        return viscosity
    def get_viscosity(P, T):
        return gas_vis(P, T)
    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis
    specific_heat = 2303.56
    
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)

if __name__ == '__main__':
    flu = create_flu()