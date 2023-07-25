"""
Created on Sat Jan 21 09:45:19 2023

@author: Maryelin
"""
""" critical values akes from Yaw's table
C22H46 = Dodecane
PM = KG/MOL
R = J/MOL*K
Tc= K
PC=Pa
w = adimentional
"""
"peng-robinson EOS"

import numpy as np


def den_c22h46(P, T):
    PM = 0.310607
    R = 8.314472
    Tc = 791.32
    Pc = 0.902e6
    w = 0.751

    Tr = T / Tc

    a1 = ((R ** 2) * (Tc ** 2)) / Pc
    b = (0.07780 * R * Tc) / Pc
    k = (0.37646) + (1.54226 * w) - (0.26992 * (w ** 2))

    alpha = 0.45724 * np.power((1 + k * (1 - np.power(Tr, 1 / 2))), 2)
    a = alpha * a1

    c = 2
    d = -1

    A = (b * (c - 1)) - ((R * T) / P)

    B = ((b ** 2) * (d - c)) - (((R * T) / P) * c * b) + (a / P)

    C = - (d * b ** 2) * (b + ((R * T) / P)) + ((a * b) / P)

    v_coef = [1, A, B, C]
    v_ = np.roots(v_coef)
    den = (1 / v_.real[1]) * PM
    return den
