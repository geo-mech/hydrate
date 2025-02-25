# -*- coding: utf-8 -*-
"""
@author: Maryelin

Specific Heat of Oxigen Gas  from:
https://www.engineeringtoolbox.com/carbon-monoxide-d_1416.html
"""
import warnings

from zml import Interp2, Seepage
from zmlx.fluid.conf.gas_density.CO_density import *
from zmlx.fluid.conf.gas_viscosity.CO_viscosity import *


def create(tmin=280, tmax=700, pmin=1.0e6, pmax=20.0e6, name=None):
    assert 250 < tmin < tmax < 750
    assert 0.01e6 < pmin < pmax < 30.0e6

    def liq_den(P, T):
        density = den_co(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 280, 10, 750, get_density)
        return den

    def liq_vis(P, T):
        viscosity = gas_vis_co(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1046  # J/kg K
    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
