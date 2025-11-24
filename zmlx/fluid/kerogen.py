import zmlx.alg.sys as warnings

from zmlx.base.zml import Seepage


def create_flu_v0():
    """
    Maryelin: for kerogen density:
        Dang, S. (2016). "A new approach to measure organic density." PETROPHYSICS.


    Maryelin: For the specific heat it was a little more difficult,
            usually the specific heat of the rock shale is assumed,
            so I followed this reference that studies the specific heat of the rock with TOC

            Waples, D. W. and J. S. Waples (2004).
            "A Review and Evaluation of Specific Heat Capacities of Rocks, Minerals, and Subsurface Fluids.
            Part 1: Minerals and Nonporous Rocks." Natural Resources Research 13(2): 97-122.

    """
    den = 1500
    specific_heat = 2000
    return Seepage.FluDef(
        den=den,
        vis=1.0e30,
        specific_heat=specific_heat)


def create(name=None):
    """
    Data from Maryelin.

    Maryelin:
        This professor, because this time I made sure to look for more references that were more accurate for kerogen.
        It does not mean that the previous one are wrong, but with those articles I have better justification.
    """

    den = 2590  # kg/m3 Longmaxi FM (Baoyun Zhao 2021)
    vis = 1.0e30
    specific_heat = 829  # J/ Kg K # Longmaxi Fm. Xiang etal, 2020
    return Seepage.FluDef(
        den=den, vis=vis, specific_heat=specific_heat,
        name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    print(create())
