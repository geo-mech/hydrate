from zmlx.exts import Seepage
from zmlx.fluid.co2 import create as create_co2
from zmlx.fluid.h2o import create as create_h2o
from zmlx.fluid.solution import create_solute

from zmlx.scen.mineralization_reactor._config import (
    AQUEOUS_COMPONENTS,
    DEFAULT_DATABASE,
    DEFAULT_STATE,
    MINERALS,
    mineral_density,
)


def create_fludefs(database=DEFAULT_DATABASE):
    h2o = create_h2o(name='h2o')

    gas = Seepage.FluDef(name='gas')
    gas.add_component(create_co2(name='co2_gas'), name='co2_gas')

    liq = Seepage.FluDef(name='liq')
    liq.add_component(h2o, name='h2o')
    for name, species in AQUEOUS_COMPONENTS.items():
        liq.add_component(_solute(h2o, name, _mass_fraction(DEFAULT_STATE[species])), name=name)

    sol = Seepage.FluDef(name='sol')
    for item in MINERALS:
        den = item.density
        if den is None:
            den = mineral_density(item.name, database=database)
        sol.add_component(_solid(item.name, den), name=item.name)

    return [gas, liq, sol]


def _solute(solvent, name, c):
    return create_solute(solvent=solvent, name=name, c=c)


def _mass_fraction(mass):
    mass = max(float(mass), 1.0e-30)
    water = max(float(DEFAULT_STATE['H2O']), 1.0e-30)
    return min(mass / (water + mass), 0.2)


def _solid(name, den):
    return Seepage.FluDef(
        den=den,
        vis=1.0e20,
        specific_heat=850.0,
        name=name)
