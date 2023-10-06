"""
Created on Fri Jan 27 20:39:54 2023

@author: Maryelin
Yaw's correlations for gas viscosity (organic)

Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003
Original units = µP
"""

def gas_vis_c22h46(P, T):
    A = 0.6821
    B = 0.1044
    C = 0.0000011301
    viscosity = (A + B*T + (C * (T**2))) * 1.0e-7 #pa*s
    return viscosity
    