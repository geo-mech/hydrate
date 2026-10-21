# -*- coding: utf-8 -*-
"""O2 density 气体密度关联式（Yaw's table 临界值）.

Modified by Claude, 2026-08-12
"""
# critical values from Yaw's table:
# O2 = Oxygen, PM = KG/MOL
# R = J/MOL*K, Tc = K, PC = Pa, w = adimentional
# Ref: https://www.engineeringtoolbox.com/air-temperature-pressure-density-d_771.html

def den_O2(P, T):
    M = 0.031999
    R = 8.314472
    Tc = 154.58
    Pc = 5043000
    w = 0.022

    den = (P * M) / (R * T)

    return den
