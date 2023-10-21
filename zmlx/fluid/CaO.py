"""

@author: Maryelin
"""

from zml import Seepage


def create(name=None):
    """
    Calcium oxide appears as an odorless, white or gray-white solid in the form of hard lumps
    Density, MW = https://pubchem.ncbi.nlm.nih.gov/compound/Calcium-oxide
    Specific Heat = https://webbook.nist.gov/cgi/cbook.cgi?ID=C1305788&Mask=2
    liquid Phase Capacity (Shomate equation)
    Cp = 53.08 J/mol*K @ 900K
    MW = 56.08 

    """

    den = 3340
    vis = 1.0e30
    specific_heat = 946.51
    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat, name=name)


if __name__ == '__main__':
    print(create())
