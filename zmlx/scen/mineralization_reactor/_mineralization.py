from dataclasses import dataclass, field
from collections import OrderedDict
from functools import lru_cache
import json
import math
from typing import Dict, List

import reaktoro as rkt

from zmlx.scen.mineralization_reactor._config import (
    DEFAULT_SCENE,
    DEFAULT_STATE,
    FLUID_NAMES,
    MINERALS,
    STATE_SPECIES,
    ReactorConfig,
    get_database,
    species_molar_mass,
    scene_config,
    scene_state,
)

class Mineralization:
    """
    Local mineralization reactor.

    It only advances a cell chemistry dictionary by one time step. Meshes,
    wells, transport, plotting, and result export belong to the Seepage model.
    """

    model = 'base'

    def list_fluid_names(self) -> List[str]:
        return []

    def calc_next_state(
            self,
            current_state: Dict[str, float],
            time_step: float,
            temperature: float,
            pressure: float) -> Dict[str, float]:
        return dict(current_state or {})

    def to_text(self) -> str:
        return json.dumps({'model': self.model}, separators=(',', ':'))

    @staticmethod
    def from_text(text: str):
        data = parse_text(text)
        if data.get('model', Co2StorageMineral.model) == Co2StorageMineral.model:
            return Co2StorageMineral(
                scene=data.get('scene', DEFAULT_SCENE),
                database=data.get('db', data.get('database')),
                surface_area=data.get('sa', data.get('surface_area')))
        return Mineralization()


@dataclass
class Co2StorageMineral(Mineralization):
    """
    CO2-brine-mineral kinetic reactor for one Seepage cell.
    """

    scene: str = DEFAULT_SCENE
    database: str = None
    surface_area: float = None
    model: str = 'co2_storage_mineral'
    _config: ReactorConfig = field(default=None, init=False, repr=False, compare=False)
    _default_state: dict = field(default=None, init=False, repr=False, compare=False)
    _system: object = field(default=None, init=False, repr=False, compare=False)
    _solver: object = field(default=None, init=False, repr=False, compare=False)
    _molar_masses: dict = field(default=None, init=False, repr=False, compare=False)
    _state_cache: object = field(default_factory=OrderedDict, init=False, repr=False, compare=False)

    def __post_init__(self):
        self._config = scene_config(self.scene, self.database, self.surface_area)
        self.scene = self._config.scene
        self.database = self._config.database
        self.surface_area = self._config.surface_area
        self._default_state = scene_state(self.scene)
        self._molar_masses = self._create_molar_mass_cache()
        self._system = self._create_system()
        self._solver = rkt.KineticsSolver(self._system)

    def list_fluid_names(self) -> List[str]:
        return list(FLUID_NAMES)

    @property
    def system(self):
        if self._system is None:
            self._system = self._create_system()
        return self._system

    @property
    def solver(self):
        if self._solver is None:
            self._solver = rkt.KineticsSolver(self.system)
        return self._solver

    def _create_system(self):
        return _cached_system(self.database, max(float(self.surface_area), 0.0))

    def _create_molar_mass_cache(self):
        masses = {'CO2(g)': species_molar_mass('CO2(g)', self.database)}
        for mineral in MINERALS:
            masses[mineral.phase] = species_molar_mass(mineral.phase, self.database)
        return masses

    def _new_state(self, state: Dict[str, float], temperature, pressure):
        water = _positive(state.get('H2O', self._default_state['H2O']), self._default_state['H2O'])
        chemical = rkt.ChemicalState(self.system)
        chemical.temperature(float(temperature), 'K')
        chemical.pressure(max(float(pressure), 1.0e5), 'Pa')
        chemical.set('H2O(aq)', water, 'kg')
        for name in STATE_SPECIES:
            if name == 'H2O':
                continue
            chemical.set(name, _positive(state.get(name, self._default_state[name])), 'kg')
        for mineral in MINERALS:
            chemical.set(
                mineral.phase,
                max(_positive(state.get(mineral.phase, self._default_state[mineral.phase])), 1.0e-30),
                'kg')
        return chemical, water

    def calc_next_state(
            self,
            current_state: Dict[str, float],
            time_step: float,
            temperature: float,
            pressure: float) -> Dict[str, float]:
        state0 = self._with_defaults(current_state)
        state1 = dict(state0)
        dt = max(float(time_step), 1.0e-12)
        cache_key = self._cache_key(state0, dt, temperature, pressure)
        cached = self._state_cache.get(cache_key)
        if cached is not None:
            self._state_cache.move_to_end(cache_key)
            return dict(cached)

        initial = {m.phase: _positive(state0.get(m.phase, 0.0)) for m in MINERALS}
        chemical, water = self._new_state(state0, temperature, pressure)
        try:
            result = self.solver.solve(chemical, dt)
        except Exception as err:
            state1['reaktoro_succeeded'] = 0.0
            state1['reaktoro_error'] = str(err)
            return state1
        if hasattr(result, 'succeeded') and not result.succeeded():
            state1['reaktoro_succeeded'] = 0.0
            return state1

        props = chemical.props()
        aprops = rkt.AqueousProps.compute(props)
        state1['H2O'] = water
        state1['reaktoro_succeeded'] = 1.0
        state1['pH'] = _value(lambda: aprops.pH(), state0.get('pH', 7.0))
        for name in STATE_SPECIES:
            if name == 'H2O':
                continue
            state1[name] = _value(lambda n=name: props.speciesMass(n), state0[name])

        co2_mass = self._molar_masses['CO2(g)']
        fixed_kg = 0.0
        released_kg = 0.0
        for mineral in MINERALS:
            amount = _value(lambda p=mineral.phase: props.speciesMass(p), initial[mineral.phase])
            delta = amount - initial[mineral.phase]
            carbon = delta / self._molar_masses[mineral.phase] * mineral.carbon
            carbon_kg = carbon * co2_mass
            fixed_kg += max(carbon_kg, 0.0)
            released_kg += max(-carbon_kg, 0.0)
            state1[mineral.phase] = amount
            state1[f'{mineral.phase}_delta_kg'] = delta
            state1[f'{mineral.phase}_rate_kg_s'] = delta / dt
            state1[f'{mineral.phase}_si'] = _value(
                lambda p=mineral.phase: aprops.saturationIndex(p), float('nan'))
        state1['CO2_fixed_kg'] = fixed_kg
        state1['CO2_released_kg'] = released_kg
        state1['mineralization_rate_kg_s'] = fixed_kg / dt
        self._remember_state(cache_key, state1)
        return state1

    def to_text(self) -> str:
        return (
            f'model={self.model};scene={self.scene};'
            f'db={self.database};sa={self.surface_area:g}')

    def _with_defaults(self, state):
        result = dict(self._default_state)
        if state:
            for key, value in state.items():
                if value is not None:
                    result[key] = value
        return result

    def _cache_key(self, state, dt, temperature, pressure):
        items = tuple(
            sorted((str(key), _cache_value(value)) for key, value in state.items()))
        return (
            float(dt),
            float(temperature),
            max(float(pressure), 1.0e5),
            items)

    def _remember_state(self, key, state):
        self._state_cache[key] = dict(state)
        self._state_cache.move_to_end(key)
        while len(self._state_cache) > 64:
            self._state_cache.popitem(last=False)


@lru_cache(maxsize=16)
def _cached_system(database, surface_area):
    db = get_database(database)
    params = _reaction_params()
    aqueous = rkt.AqueousPhase(rkt.speciate('H O C Ca Mg Na K Al Si Cl S'))
    aqueous.set(rkt.ActivityModelPitzer())
    gas = rkt.GaseousPhase('CO2(g)')
    gas.set(rkt.ActivityModelPengRobinsonPhreeqcOriginal())

    args = [db, aqueous, gas, rkt.MineralPhases(' '.join(m.phase for m in MINERALS))]
    for mineral in MINERALS:
        args.append(
            rkt.MineralReaction(mineral.phase).setRateModel(
                rkt.ReactionRateModelPalandriKharaka(params)))
        args.append(rkt.MineralSurface(
            mineral.phase, surface_area, 'cm2/cm3'))
    return rkt.ChemicalSystem(*args)


@lru_cache(maxsize=1)
def _reaction_params():
    return rkt.Params.embedded('PalandriKharaka.yaml')


def parse_text(text: str):
    text = (text or DEFAULT_SCENE).strip()
    if not text:
        text = DEFAULT_SCENE
    if text.startswith('{'):
        data = json.loads(text)
        if 'scene' not in data and 'preset' in data:
            data['scene'] = data['preset']
        return data
    if '=' not in text and ';' not in text:
        return {'model': Co2StorageMineral.model, 'scene': text}
    data = {}
    for item in text.split(';'):
        item = item.strip()
        if not item:
            continue
        key, value = item.split('=', 1)
        data[key.strip()] = value.strip()
    data.setdefault('model', Co2StorageMineral.model)
    data.setdefault('scene', DEFAULT_SCENE)
    return data


def _positive(value, default=0.0):
    try:
        value = float(value)
    except Exception:
        value = float(default)
    if not math.isfinite(value):
        value = float(default)
    return max(value, 0.0)


def _value(fn, default=0.0):
    try:
        value = float(fn())
    except Exception:
        return float(default)
    return value if math.isfinite(value) else float(default)


def _cache_value(value):
    try:
        number = float(value)
    except Exception:
        return 'text', repr(value)
    if math.isfinite(number):
        return 'number', number
    return 'text', repr(value)
