# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 20:25:43 2023

@author: Maryelin
"""

"fluid properties"

from zmlx.fluid.conf.gas_density import *
from zmlx.fluid.conf.liqu_density import *
from zmlx.fluid.conf.gas_viscosity import *
from zmlx.fluid.conf.liqu_viscosity import *
from zmlx.fluid.conf.aqueos import *

"""
Properties of Fluids present in the kerogen decomposition pyrolysis
lee 2014
h2o = water
iC22 = heavy oil
iC2 = ethane
h2 = hydrogen
co2 = carbonate dioxide
"""

"""
Heat Capacity:
https://www.chemeo.com/cid/25-097-7/Docosane
https://www.chemeo.com/cid/31-101-4/Ethane
https://www.chemeo.com/cid/25-906-8/Carbon-dioxide
"""

"H2O"


def h2o_steam(tmin=280, tmax=1000, pmin=1.0e6, pmax=40.0e6):
    def den_steam(P, T):  # units p = Pa
        density = den_h2o(P, T)
        return density

    def get_density(P, T):
        return den_steam(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def vis_steam(P, T):  # units p = Pa
        viscosity = gas_vis_h2o(P, T)
        return viscosity

    def get_viscosity(P, T):
        return vis_steam(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1850.0
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


def h2o_liq(tmin=280, tmax=1000, pmin=1.0e6, pmax=40.0e6):
    def den_liq(P, T):  # units p = Pa
        density = liq_den_h2o(P, T)
        return density

    def get_density(P, T):
        t = max(tmin, min(tmax, T))
        return den_liq(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def vis_liq(P, T):  # units p = Pa
        viscosity = liq_vis_h2o(P, T)
        return viscosity

    def get_viscosity(P, T):
        return vis_liq(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 4200.0
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


"C22H46 (Docosane)"

def iC22_gas(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    def gas_den(P, T):
        density = den_c22h46(P, T)
        return density

    def get_density(P, T):
        return gas_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_c22h46(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 3097.30  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


def iC22_liqu(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    def liq_den(P, T):
        density = liq_den_c22h46(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 280, 10, 750, get_density)
        return den

    def liq_vis(P, T):
        viscosity = liq_vis_c22h46(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 2379.27  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)

"C11H24"
def iC11_gas(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    def gas_den(P, T):
        density = den_c11h24(P, T)
        return density
    def get_density(P, T):
        return gas_den(P, T)
    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, 900, get_density)
        return den  
    def gas_vis(P, T):
        viscosity = gas_vis_c11h24(P, T)
        return viscosity
    def get_viscosity(P, T):
        return gas_vis(P, T)
    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis
    specific_heat = 2303.56
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)

def iC11_liq(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):   
    def liq_den(P, T):
        density = liq_den_c11h24(P,T)
        return density
    def get_density(P, T):
        return liq_den(P, T)
    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 100, 10, 600, get_density)
        return den
    def liq_vis(P, T):
        viscosity = liq_vis_c11h24(P, T)
        return viscosity
    def get_viscosity(P, T):
        return liq_vis(P, T)
    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis  
    specific_heat = 2157.82 #J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


"C2H6 (ethane)"

def iC2_gas(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
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


def iC2_liqu(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
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


"H2"


def H2_gas(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    def gas_den(P, T):
        density = den_h2(P, T)
        return density

    def get_density(P, T):
        return gas_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_h2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 14304  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


def H2_liq(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    def liq_den(P, T):
        density = liq_den_h2(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def liq_vis(P, T):
        viscosity = liq_vis_h2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 14304  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


"CO2"


def co2_gas(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    # def gas_den(P, T):
    #     return density

    def get_density(P, T):
        return den_co2(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_co2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 738.69  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


def co2_liq(tmin=280, tmax=2000, pmin=1.0e6, pmax=40.0e6):
    # def liq_den(P, T):
    #     density = liq_den_co2(P, T)
    #     return density

    def get_density(P, T):
        return liq_den_co2(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 20, 10, 280, get_density)
        return den

    def liq_vis(P, T):
        viscosity = liq_vis_co2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 2232  # J/kg K
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


"Kerogen"


def kerogen():
    den = 2590  # kg/m3 Longmaxi FM (Baoyun Zhao 2021)
    vis = 1.0e30
    specific_heat = 829  # J/ Kg K # Longmaxi Fm. Xiang etal, 2020
    return TherFlowConfig.FluProperty(den=den, vis=vis, specific_heat=specific_heat)


"char = coal gas"


def char():
    den = 1100  # kg/m3
    vis = 1.0e30
    specific_heat = 1380
    return TherFlowConfig.FluProperty(den=den, vis=vis, specific_heat=specific_heat)



def show_all():
    from zmlx.plt.show_field2 import show_field2
    flu = h2o_steam()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='h2o_steam.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='h2o_steam.vis')

    # !!! 水的数据在温度比较高的时候出现异常！
    flu = h2o_liq()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='h2o_liq.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='h2o_liq.vis')

    flu = iC22_gas()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='iC22_gas.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='iC22_gas.vis')

    flu = iC22_liqu()
    show_field2(flu.den, [1e6, 40e6], [280, 750], caption='iC22_liqu.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='iC22_liqu.vis')

    flu = iC2_gas()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='iC2_gas.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='iC2_gas.vis')

    flu = iC2_liqu()
    show_field2(flu.den, [1e6, 40e6], [20, 280], caption='iC2_liqu.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='iC2_liqu.vis')

    flu = H2_gas()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='H2_gas.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='H2_gas.vis')

    flu = H2_liq()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='H2_liq.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='H2_liq.vis')

    flu = co2_gas()
    show_field2(flu.den, [1e6, 40e6], [280, 1000], caption='co2_gas.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='co2_gas.vis')

    flu = co2_liq()
    show_field2(flu.den, [1e6, 40e6], [20, 280], caption='co2_liq.den')
    show_field2(flu.vis, [1e6, 40e6], [280, 1000], caption='co2_liq.vis')


if __name__ == '__main__':
    from zml import gui
    gui.execute(show_all, close_after_done=False)





