# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 15:18:22 2023

@author: Maryelin
#prof Zhang

"""

import math

def liq_vis_h2o(P,T):
    viscosity = 2.0E-6 * math.exp(1808.5 / T)
    return viscosity