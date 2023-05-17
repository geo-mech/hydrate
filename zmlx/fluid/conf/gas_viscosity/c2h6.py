# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 20:48:09 2023

@author: Maryelin
Yaw's correlations for gas viscosity (organic)

Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003
"""

def gas_vis_c2h6(P, T):
    A = 0.5142
    B = 0.3345
    C = -0.000071071
    viscosity = (A + B*T + (C * (T**2))) * 1.0e-7 #pa*s
    return viscosity