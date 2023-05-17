# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 17:34:56 2023

@author: Maryelin
"""
"""
H2O

https://github.com/drunsinn/pyXSteam

XSteam provides (mostly) accurate steam and water properties
from 0 - 1000 bar and from 0 - 2000 °C
according to the IAPWS release IF-97.

Also includes thermal conductivity and viscosity,

"""

from pyXSteam.XSteam import XSteam

def den_h2o(P, T): # units p = Pa
        pressure = P * (1 / 1000000)
        steamTable = XSteam(XSteam.UNIT_SYSTEM_BARE) # m/kg/sec/K/MPa/W
        density = steamTable.rho_pt(pressure, T)
        return density 
    
