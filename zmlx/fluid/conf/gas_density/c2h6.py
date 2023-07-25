"""
Created on Sat Jan 21 09:45:19 2023

@author: Maryelin
"""
""" critical values from Yaw's table
C2H6 = Ethane
PM = KG/MOL
R = J/MOL*K
Tc= K
PC=Pa
w = adimentional
"""
"Redlich-kwong EOS"
import numpy as np


def den_c2h6(P, T):
    PM = 0.03007
    R = 8.314472
    Tc = 305.42
    Pc = 4.88e6
    w = 0.099

    a = 0.42780 * ((R ** 2) * (Tc ** 2.5)) / Pc
    b = 0.086640 * (R * Tc) / Pc

    # MOLAR VOLUME
    A = - (R * T) / P

    B = (1 / P * T ** 0.5) - ((b * R * T) / P) - (b ** 2)

    C = - (a * b) / (P * T ** 0.5)

    "v_equ = v**3 + A * v**2 + B * v + C"

    v_coef = [1, A, B, C]
    v_ = np.roots(v_coef)

    den = (1 / (v_.real[0])) * PM

    return den
