# -*- coding: utf-8 -*-
"""
Created on Sun Jun 11 12:08:13 2023

@author: Maryelin
"""

import zmlx.react.Solid_deshydra as deshydratation
from zml import Interp1, data_version
import numpy as np

"""
vt, vp 
Kinetics of the CaO/Ca(OH)2 Hydration/Dehydration Reaction for
Thermochemical Energy Storage Applications
by https://doi.org/10.1021/ie404246p

"""

vt = [float(i) for i in range(723, 823)]
vp = [2.30e8 * np.exp(-11607 / t ) * 1000 for t in vt]


def create_t2p():
    return Interp1(x=vt, y=vp).to_evenly_spaced(300)


def create_p2t():
    return Interp1(x=vp, y=vt).to_evenly_spaced(300)


def get_mg_vs_mh():
    """
    Returns the mass of Calcium Carbonate produced after 1kg of  Ca(OH)2 dehydrate
    Ca(OH)2 (s) ↔ CaO (s)+ H2O (g)
    1 mol of Ca(OH)2 produce 1 mol of CaO
    """
    return 56.077e-3 / 74.093e-3


def get_dheat():
    """
    Calories consumed to deshidrate 1kg of Calcium Hydroxide
     ---
     Ca(OH)2 (s) ↔ CaO (s)+ H2O (g) ∆H = 104.4 kJ/mol
     by https://doi.org/10.3390/en16073019
    """
    if data_version.CaOH2_deshydra >= 221029:
        return (104.4e3 / 74.093E-3) * get_mg_vs_mh()
    else:
        return (104.4e3 / 74.093E-3) * get_mg_vs_mh()


def create(iCaOH2, iwat, iCaO, fa_t, fa_c):
    """
    Under atmospheric pressure, the heat storage temperature of
    Ca(OH)2 ranges from 400 to 600 ◦C, and the heat release temperature ranges from 25 ◦C to
    approximately 500 ◦C (as determined from the partial pressure of the steam involved in the reaction)
    by https://doi.org/10.3390/su10082660
    """
    return deshydratation.create(vp=vp, vt=vt, temp=(500 + 273.15), heat=get_dheat(),
                          mg=get_mg_vs_mh(),
                          isol_d=iCaOH2, iliq=iwat, isol=iCaO,
                          fa_t=fa_t, fa_c=fa_c)