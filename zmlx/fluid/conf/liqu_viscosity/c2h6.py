"""
Created on Fri Jan 27 19:04:15 2023

@author: Maryelin

Yaws, C. Yaws’ Handbook of Thermodynamic and Physical Properties of Chemical
Compounds, Knovel, 2003


"""

def liq_vis_c2h6(P, T):
    A = -4.2694
    B = 289.54
    C = 0.0171
    D = -0.000036092
    log10_vis = A + B/T + C*T + D*(T**2) ##Yaw's correlations
    vis = (10 ** (log10_vis)) * 0.001 #pa*sec
    return vis