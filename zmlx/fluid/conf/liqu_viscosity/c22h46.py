# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 18:44:51 2023

@author: Maryelin

Mehrotra, Anil K and Svrcek, William Y, The Canadian Journal of Chemical Engineering, 1986
Viscosity oof Compressed Athabasca Bitumen
"""

import numpy as np

def liq_vis_c22h46(P, T): #Mehrotra and Svrcek, 1986
    b1 = 22.8515
    b2 = -3.5784
    b3 = int(0.00511938)
    A = (b1 + (b2 * np.log(T))) + (b3 * (P * 0.000001))
    vis_oil = 0.001 * (np.exp(np.exp(A)))
    return vis_oil