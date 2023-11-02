# -*- coding: utf-8 -*-
""" critical values akes from Yaw's table
CO2 = Carbon Dioxide
PM = KG/MOL
R = J/MOL*K
Tc= K
PC=Pa
w = adimentional
"""

import numpy as np

def den_co(P, T):
        PM = 0.02801
        R = 8.314472
        Tc = 132.92
        Pc = 3.499e6
        w = 0.066
                      
        a = 0.42780 * ((R **2) * (Tc**2.5)) / Pc
        b = 0.086640 * (R *  Tc) / Pc
              
        # MOLAR VOLUME
        A = - (R * T) / P     
        B = (1 / P * T**0.5) - ((b * R * T) / P) - (b**2)       
        C = - (a * b) / (P * T**0.5)
        
        "v_equ = v**3 + A * v**2 + B * v + C"
   
        v_coef = [1, A, B, C]
        v_ = np.roots(v_coef)
        
        den = (1 / (v_.real[0])) * PM
        
        return den
