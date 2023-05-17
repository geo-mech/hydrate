# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 19:44:06 2023

@author: Maryelin


Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003

"""

def liq_vis_co2(P, T):
    A = -19.492
    B = 1594.8
    C = 0.0793
    D = -0.00012025
    log10_vis = A + B/T + C*T + D*(T**2) ##Yaw's correlations
    vis = (10 ** (log10_vis)) * 0.001 #pa*sec
    return vis
