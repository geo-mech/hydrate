"""
Created on Fri Jan 27 20:39:54 2023

@author: Maryelin
Yaw's correlations for gas viscosity (organic)

Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003
3,4-diethylheptane
original units = µP
"""

def gas_vis_c11h24(P, T):
    A = -3.8819
    B = 0.1874
    C = -0.000019892
    viscosity = (A + B*T + (C * (T**2))) * 1.0e-7 #pa*s
    return viscosity