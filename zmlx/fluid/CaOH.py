# -*- coding: utf-8 -*-
"""

@author: Maryelin
"""
from zml import TherFlowConfig

def create_flu():
    
    """
    Density, MW = https://kemicalinfo.com/chemicals/calcium-hydroxide-caoh2/
    Specific Heat = https://webbook.nist.gov/cgi/cbook.cgi?ID=C1305620&Mask=FFF&Type=JANAFS&Plot=on#JANAFS
    liquid Phase Capacity (Shomate equation)
    Cp = 116.0 J/mol*K @ 900K
    MW = 74.09 g/mol 

    """

    den = 2240
    vis = 1.0e30
    specific_heat = 1565.66  
    return TherFlowConfig.FluProperty(den=den, vis=vis, specific_heat=specific_heat)


if __name__ == '__main__':
    print(create_flu())

