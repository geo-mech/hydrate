
"""
Create a reversible reaction of <(Ca(OH)2)> dehydration and <(CaO)> hydration.
During dehydratation process (heat storage), <(Ca(OH)2)> absorbs heat and decomposes to produce <(CaO)> and <(H2O)>.
In the exothermic process, <(CaO)> reacts with <(H2O)> to form <(Ca(OH)2)>, 
releasing stored chemical energy as heat.
by Maryelin

"""
import zmlx.react.endothermic as endothermic
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


def get_mca_vs_mcaoh():
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
    return (104.4e3 / 74.093E-3) * get_mca_vs_mcaoh()
    

def create(iCaOH2, iliq, iCaO, fa_t, fa_c):
    """
    Under atmospheric pressure, the heat storage temperature of
    Ca(OH)2 ranges from 400 to 600 ◦C, and the heat release temperature ranges from 25 ◦C to
    approximately 500 ◦C (as determined from the partial pressure of the steam involved in the reaction)
    by https://doi.org/10.3390/en16073019
    """
    return endothermic.create(left=[(iCaOH2, 1.0), ],
                              right=[(iCaO, get_mca_vs_mcaoh()), (iliq, 1.0 - get_mca_vs_mcaoh())],
                              temp=(500 + 273.15), heat=get_dheat(),
                              rate=1.0,
                              fa_t=fa_t, fa_c=fa_c,
                              l2r=True, r2l=True,
                              p2t=[vp, vt], t2q=None)
