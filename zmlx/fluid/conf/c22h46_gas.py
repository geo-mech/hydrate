"""

C2H22 = Docosane
Heavy Oil 

"""

import zmlx.alg.sys as warnings

from zmlx.exts.base import Interp2, Seepage
from zmlx.fluid.conf.gas_density.c22h46 import den_c22h46
from zmlx.fluid.conf.gas_viscosity.c22h46 import gas_vis_c22h46


def create(tmin=280, tmax=1000, pmin=1.0e6, pmax=30.0e6, name=None):
    assert 250 < tmin < tmax < 1500
    assert 0.01e6 < pmin < pmax < 40.0e6

    def gas_den(P, T):
        density = den_c22h46(P, T)
        return density

    def get_density(P, T):
        return gas_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def gas_vis(P, T):
        viscosity = gas_vis_c22h46(P, T)
        return viscosity

    def get_viscosity(P, T):
        return gas_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 3097.30  # J/kg K
    return Seepage.FluDef(den=create_density(), vis=create_viscosity(),
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
