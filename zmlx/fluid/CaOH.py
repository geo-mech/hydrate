"""

@author: Maryelin
"""
from zml import Seepage


def create(name=None):
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
    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat, name=name)


if __name__ == '__main__':
    print(create())
