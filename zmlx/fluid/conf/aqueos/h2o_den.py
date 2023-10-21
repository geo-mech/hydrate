"""
Created on Mon Jan 30 14:55:00 2023

@author: Maryelin
Prof Zhang

"""

import math


def liq_den_h2o(P, T):
    density = 999.8 * (1.0 + (P / 2000.0E6)) * (1.0 - 0.0002 * math.pow((T - 277.0) / 5.6, 2))
    return density
