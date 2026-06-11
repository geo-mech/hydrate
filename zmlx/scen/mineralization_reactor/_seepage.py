from functools import lru_cache
import math

from zmlx.exts import Seepage
from zmlx.tfc import get_dt, step_iteration

from zmlx.scen.mineralization_reactor._config import (
    AQUEOUS_COMPONENTS,
    DEFAULT_DATABASE,
    FIELD_NAMES,
    MINERAL_COMPONENTS,
    STATE_TO_FIELD,
)
from zmlx.scen.mineralization_reactor._mineralization import (
    Co2StorageMineral,
    Mineralization,
)


def key_fields(model: Seepage):
    return {name: model.reg_cell_key(name) for name in FIELD_NAMES}


def add_to_model(model: Seepage, mineralization=None):
    if mineralization is None:
        mineralization = Co2StorageMineral()
    text = mineralization if isinstance(mineralization, str) else mineralization.to_text()
    model.set_text('Mineralization', text)
    step_iteration.add_setting(
        model, start=0, step=1, stop=999999999,
        name='mineralization_reaction', args=['@model'])
    return model


def mineralization_reaction(model: Seepage, time_step=None):
    mineralization = _from_text(model.get_text('Mineralization'))
    database = getattr(mineralization, 'database', DEFAULT_DATABASE)
    dt = get_dt(model) if time_step is None else float(time_step)
    keys = key_fields(model)
    count = 0
    for cell in model.cells:
        state0 = state_from_cell(cell, database=database)
        state1 = mineralization.calc_next_state(
            current_state=state0,
            time_step=dt,
            temperature=_cell_temperature(model, cell),
            pressure=max(cell.pre, 1.0e5))
        write_state_to_cell(cell, state1, database=database)
        write_state_to_attrs(cell, keys, state1)
        count += 1
    return count


def state_from_cell(cell: Seepage.Cell, database=DEFAULT_DATABASE):
    water = max(component(cell, 'h2o').mass, 1.0e-30)
    state = {
        'H2O': water,
        'CO2(g)': component(cell, 'co2_gas').mass,
    }
    for name, species in AQUEOUS_COMPONENTS.items():
        state[species] = component(cell, name).mass
    for name, phase in MINERAL_COMPONENTS.items():
        state[phase] = component(cell, name).mass
    return state


def write_state_to_cell(cell: Seepage.Cell, state, database=DEFAULT_DATABASE):
    if 'H2O' in state:
        set_component_mass(cell, 'h2o', state['H2O'])
    if 'CO2(g)' in state:
        set_component_mass(cell, 'co2_gas', float(state['CO2(g)']))
    for name, species in AQUEOUS_COMPONENTS.items():
        if species in state:
            set_component_mass(cell, name, float(state[species]))
    for name, phase in MINERAL_COMPONENTS.items():
        if phase in state:
            set_component_mass(cell, name, float(state[phase]))


def write_state_to_attrs(cell: Seepage.Cell, keys, state):
    for key in ('pH', 'reaktoro_succeeded', 'mineralization_rate_kg_s'):
        if key in state and key in keys:
            cell.set_attr(keys[key], _finite(state[key]))
    for state_name, field_name in STATE_TO_FIELD.items():
        if state_name in state and field_name in keys:
            cell.set_attr(keys[field_name], _finite(state[state_name]))


def component(cell: Seepage.Cell, name: str):
    fid = cell.model.find_fludef(name)
    if fid is None:
        raise KeyError(f'fluid/component "{name}" is required by Mineralization')
    return cell.get_fluid(*fid)


def set_component_mass(cell: Seepage.Cell, name: str, mass: float):
    comp = component(cell, name)
    comp.mass = max(_finite(mass), 0.0)
    den = getattr(comp, 'den', 0.0)
    if den > 0.0:
        comp.vol = comp.mass / den


def _cell_temperature(model, cell):
    key = model.get_cell_key('temperature')
    if key is None:
        return cell.get_attr('temperature_K', default_val=298.15)
    return cell.get_attr(key, default_val=298.15)


def _finite(value, default=0.0):
    try:
        value = float(value)
    except Exception:
        return default
    return value if math.isfinite(value) else default


@lru_cache(maxsize=32)
def _from_text(text):
    return Mineralization.from_text(text)
