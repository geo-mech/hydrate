# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 15:47:59 2023

@author: Maryelin
"""
from pyXSteam.XSteam import XSteam

def gas_vis_h2o(P, T):
    pressure = P * (1 / 1000000)
    steamTable = XSteam(XSteam.UNIT_SYSTEM_BARE) # /kg/sec/K/MPa/W
    viscosity = steamTable.my_pt(pressure, T)
    return viscosity