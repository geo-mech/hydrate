"""
Created on Fri Jan 27 21:11:02 2023

@author: Maryelin
Yaw's correlations for gas viscosity (organic)

Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003

"""


def gas_vis_co2(P, T):
    A = 11.811
    B = 0.4984
    C = -0.00010851
    viscosity = (A + B * T + (C * (T ** 2))) * 1.0e-7  # pa*s
    return viscosity
