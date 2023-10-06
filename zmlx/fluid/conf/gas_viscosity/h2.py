"""
Created on Fri Jan 27 20:53:56 2023

@author: Maryelin

Yaw's correlations for gas viscosity (organic)

Sutherlan's law is an aproximation for how the viscosity of gases depends on temperature
can be use to derive the dinamic viscosity of a ideal gas.

https://doc.comsol.com/5.5/doc/com.comsol.help.cfd/cfd_ug_fluidflow_high_mach.08.27.html

"""

def gas_vis_h2(P, T):
    t_ref = 273
    vis_ref = 8.411e-5
    s_ref=  97
    viscosity = vis_ref * ((T / t_ref)**(3/2) * ((t_ref + s_ref)/(T + s_ref))) #Sutherlands's equation for ideal gas
    return viscosity
    

