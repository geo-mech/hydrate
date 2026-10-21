# -*- coding: utf-8 -*-
"""CO density 气体密度关联式（Yaw's table 临界值）.

Modified by Claude, 2026-08-12
"""
# critical values from Yaw's table:
# CO = Carbon Monoxide, PM = KG/MOL
# R = J/MOL*K, Tc = K, PC = Pa, w = adimentional

from zmlx.exts import np


def den_co(P, T):
    PM = 0.02801
    R = 8.314472
    Tc = 132.92
    Pc = 3.499e6
    w = 0.066

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
