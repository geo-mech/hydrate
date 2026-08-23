# -*- coding: utf-8 -*-
"""CO 气体粘度关联式（Yaw’s correlations for gas viscosity）.

@author: Maryelin
Ref: Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical

Modified by Claude, 2026-08-12
"""
# Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
# Compounds, Knovel, 2003

def gas_vis_co(P, T):
    A = 23.811
    B = 0.5394
    C = -0.00015411
    viscosity = (A + B * T + (C * (T ** 2))) * 1.0e-7  # pa*s
    return viscosity
