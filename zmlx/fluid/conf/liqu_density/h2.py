"""
Created on Thu Jan 26 18:50:17 2023

@author: Maryelin

NO IDEAL GAS EQUATION

"""


def liq_den_h2(P, T):
    R = 8.314472
    Z = 0.305  # assume the critical compresibility
    PM = 2.016e-3  # Kg/mol
    density = PM * (P / (Z * R * T))
    return density
