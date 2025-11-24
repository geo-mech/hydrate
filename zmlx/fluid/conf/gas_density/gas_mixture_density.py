# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 09:10:40 2023

@author: Maryelin
the density of a gas mixture obtained from heavy oil upgrading
by 10.1016/j.petrol.2020.107850
"""

from zmlx.base.zml import np


def GAS_den(P, T):
    """
    Table 4, produce gas composition
    """
    mol = [0.499 / 100, 86.802 / 100, 0.426 / 100, 8.541 / 100, 1.331 / 100,
           0.923 / 100, 0.476 / 100]
    MW = [2.016 / 1000, 28.013 / 1000, 44.01 / 1000, 16.043 / 1000,
          30.07 / 1000, 44.097 / 1000, 58.123 / 1000]
    TC = [33.18, 126.10, 304.19, 190, 305.42, 369.82, 425.18]
    PC = [13.13 * 1.0e5, 33.94 * 1.0e5, 73.82 * 1.0e5, 46.04 * 1.0e5,
          48.8 * 1.0e5, 42.49 * 1.0e5, 37.97 * 1.0e5]
    WC = [-0.22, 0.04, 0.228, 0.011, 0.099, 0.152, 0.199]

    Msc = sum(np.multiply(mol, MW))
    Tsc = sum(np.multiply(mol, TC))
    Psc = sum(np.multiply(mol, PC))
    Wsc = sum(np.multiply(mol, WC))

    PM = Msc
    R = 8.314472
    Tc = Tsc
    Pc = Psc
    w = Wsc

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
