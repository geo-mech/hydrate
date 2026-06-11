from zmlx.seepage_mesh import create_cube
from zmlx.tfc import create as create_tfc

from zmlx.scen.mineralization_reactor._config import (
    AQUEOUS_COMPONENTS,
    DEFAULT_DATABASE,
    DEFAULT_STATE,
)
from zmlx.scen.mineralization_reactor._fluid import create_fludefs
from zmlx.scen.mineralization_reactor._mineralization import Co2StorageMineral, Mineralization
from zmlx.scen.mineralization_reactor._seepage import (
    add_to_model,
    component,
    key_fields,
    write_state_to_attrs,
    write_state_to_cell,
)


def create(
        shape=(2, 1, 1),
        size=(20.0, 1.0, 5.0),
        porosity=0.25,
        perm=1.0e-14,
        pore_modulus=100.0e6,
        temperature=298.15,
        pressure=1.0e7,
        mineralization=None,
        state_ini=None):
    if mineralization is None:
        mineralization = Co2StorageMineral()
    elif isinstance(mineralization, str):
        mineralization = Mineralization.from_text(mineralization)
    database = getattr(mineralization, 'database', DEFAULT_DATABASE)

    mesh = create_cube(
        x=_nodes(0.0, size[0], shape[0]),
        y=_nodes(0.0, size[1], shape[1]),
        z=_nodes(-size[2], 0.0, shape[2]))
    model = create_tfc(
        mesh=mesh,
        fludefs=create_fludefs(database=database),
        has_solid=True,
        porosity=porosity,
        pore_modulus=pore_modulus,
        p=pressure,
        temperature=temperature,
        perm=perm,
        dt_max=24.0 * 3600.0,
        s=_create_s_ini())
    add_to_model(model, mineralization)

    state_ini = create_state_ini() if state_ini is None else state_ini
    keys = key_fields(model)
    for cell in model.cells:
        state = state_ini(*cell.pos)
        state = _scale_state_to_cell_water(cell, state)
        write_state_to_cell(cell, state, database=database)
        write_state_to_attrs(cell, keys, state)
    return model


def create_state_ini(
        co2_aq=DEFAULT_STATE['CO2(aq)'],
        co2_gas=DEFAULT_STATE['CO2(g)'],
        ca=DEFAULT_STATE['Ca+2'],
        mg=DEFAULT_STATE['Mg+2'],
        na=DEFAULT_STATE['Na+'],
        k=DEFAULT_STATE['K+'],
        h=DEFAULT_STATE['H+'],
        oh=DEFAULT_STATE['OH-'],
        cl=DEFAULT_STATE['Cl-'],
        hco3=DEFAULT_STATE['HCO3-'],
        so4=DEFAULT_STATE['SO4-2'],
        al=DEFAULT_STATE['Al+3'],
        si=DEFAULT_STATE['SiO2(aq)']):
    def get_state(x, y, z):
        return {
            'CO2(aq)': _value(co2_aq, x, y, z),
            'CO2(g)': _value(co2_gas, x, y, z),
            'Ca+2': _value(ca, x, y, z),
            'Mg+2': _value(mg, x, y, z),
            'Na+': _value(na, x, y, z),
            'K+': _value(k, x, y, z),
            'H+': _value(h, x, y, z),
            'OH-': _value(oh, x, y, z),
            'Cl-': _value(cl, x, y, z),
            'HCO3-': _value(hco3, x, y, z),
            'SO4-2': _value(so4, x, y, z),
            'Al+3': _value(al, x, y, z),
            'SiO2(aq)': _value(si, x, y, z),
        }

    return get_state


def _create_s_ini():
    def get_s(x, y, z):
        return {
            'co2_gas': 0.02,
            'h2o': 0.84,
            'co2_aq': 0.002,
            'ca': 0.001,
            'mg': 0.001,
            'na': 0.01,
            'k': 0.001,
            'h': 1.0e-6,
            'oh': 1.0e-6,
            'cl': 0.01,
            'hco3': 0.001,
            'so4': 0.001,
            'al': 1.0e-6,
            'si': 0.001,
            'calcite': 0.035,
            'magnesite': 0.015,
            'dolomite': 0.015,
            'albite': 0.025,
            'anorthite': 0.02,
            'quartz': 0.035,
        }

    return get_s


def _nodes(start, stop, count):
    count = max(int(count), 1)
    return [start + (stop - start) * i / count for i in range(count + 1)]


def _value(value, *args):
    return value(*args) if callable(value) else value


def _scale_state_to_cell_water(cell, state):
    state = dict(state)
    if 'H2O' in state:
        return state
    water = component(cell, 'h2o').mass
    scale = max(float(water), 0.0) / max(float(DEFAULT_STATE['H2O']), 1.0e-30)
    state['H2O'] = water
    for species in AQUEOUS_COMPONENTS.values():
        if species in state:
            state[species] = float(state[species]) * scale
    return state
