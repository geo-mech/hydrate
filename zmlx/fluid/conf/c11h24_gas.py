"""


@author: Maryelin
"""

import zmlx.alg.sys as warnings

from zmlx.exts.base import Interp2, Seepage
from zmlx.fluid.conf.gas_density.c11h24 import den_c11h24
from zmlx.fluid.conf.gas_viscosity.c11h24 import gas_vis_c11h24


def create(tmin=280, tmax=850, pmin=1.0e6, pmax=20.0e6, name=None):
    assert 250 < tmin < tmax < 900
    assert 0.01e6 < pmin < pmax < 30.0e6

    def gas_den(P, T):
        density = den_c11h24(P, T)
        return density

    def get_density(P, T):
        return gas_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_c11h24(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 2303.56

    return Seepage.FluDef(den=create_density(), vis=create_viscosity(),
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
