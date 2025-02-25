# -*- coding: utf-8 -*-
""" critical values akes from Yaw's table
H2 = Hydrogen
PM = KG/MOL
R = J/MOL*K
Tc= K
PC=Pa
w = adimentional

Ideal Gas Equation, correlations results agree with this website:
https://www.engineeringtoolbox.com/air-temperature-pressure-density-d_771.html
"""


def den_O2(P, T):
    M = 0.031999
    R = 8.314472
    Tc = 154.58
    Pc = 5043000
    w = 0.022

    den = (P * M) / (R * T)

    return den
