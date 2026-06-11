from dataclasses import dataclass, replace
from functools import lru_cache

import reaktoro as rkt


DEFAULT_DATABASE = 'supcrtbl'
DEFAULT_SCENE = 'permafrost'


@dataclass(frozen=True)
class Mineral:
    name: str
    phase: str
    carbon: float = 0.0
    density: float = None


@dataclass(frozen=True)
class ReactorConfig:
    scene: str = DEFAULT_SCENE
    database: str = DEFAULT_DATABASE
    surface_area: float = 1.0e-3


MINERALS = (
    Mineral('calcite', 'Calcite', 1.0),
    Mineral('magnesite', 'Magnesite', 1.0),
    Mineral('dolomite', 'Dolomite', 2.0),
    Mineral('albite', 'Albite', 0.0),
    Mineral('anorthite', 'Anorthite', 0.0),
    Mineral('quartz', 'Quartz', 0.0),
)

STATE_SPECIES = (
    'H2O',
    'CO2(aq)',
    'CO2(g)',
    'Ca+2',
    'Mg+2',
    'Na+',
    'K+',
    'H+',
    'OH-',
    'Cl-',
    'HCO3-',
    'SO4-2',
    'Al+3',
    'SiO2(aq)',
)

AQUEOUS_COMPONENTS = {
    'co2_aq': 'CO2(aq)',
    'ca': 'Ca+2',
    'mg': 'Mg+2',
    'na': 'Na+',
    'k': 'K+',
    'h': 'H+',
    'oh': 'OH-',
    'cl': 'Cl-',
    'hco3': 'HCO3-',
    'so4': 'SO4-2',
    'al': 'Al+3',
    'si': 'SiO2(aq)',
}

MINERAL_COMPONENTS = {item.name: item.phase for item in MINERALS}

COMPONENT_SPECIES = {
    'h2o': 'H2O(aq)',
    'co2_gas': 'CO2(g)',
    **AQUEOUS_COMPONENTS,
    **MINERAL_COMPONENTS,
}

FLUID_NAMES = (
    'h2o',
    'co2_aq',
    'co2_gas',
    'ca',
    'mg',
    'na',
    'k',
    'h',
    'oh',
    'cl',
    'hco3',
    'so4',
    'al',
    'si',
    *[item.name for item in MINERALS],
)

FIELD_NAMES = (
    'pH',
    'reaktoro_succeeded',
    'co2_aq_kg',
    'co2_gas_kg',
    'ca_kg',
    'mg_kg',
    'na_kg',
    'k_kg',
    'h_kg',
    'oh_kg',
    'cl_kg',
    'hco3_kg',
    'so4_kg',
    'al_kg',
    'si_kg',
    'co2_fixed_kg',
    'co2_released_kg',
    'mineralization_rate_kg_s',
    'calcite_kg',
    'magnesite_kg',
    'dolomite_kg',
    'albite_kg',
    'anorthite_kg',
    'quartz_kg',
)

STATE_TO_FIELD = {
    'CO2(aq)': 'co2_aq_kg',
    'CO2(g)': 'co2_gas_kg',
    'Ca+2': 'ca_kg',
    'Mg+2': 'mg_kg',
    'Na+': 'na_kg',
    'K+': 'k_kg',
    'H+': 'h_kg',
    'OH-': 'oh_kg',
    'Cl-': 'cl_kg',
    'HCO3-': 'hco3_kg',
    'SO4-2': 'so4_kg',
    'Al+3': 'al_kg',
    'SiO2(aq)': 'si_kg',
    'CO2_fixed_kg': 'co2_fixed_kg',
    'CO2_released_kg': 'co2_released_kg',
    'Calcite': 'calcite_kg',
    'Magnesite': 'magnesite_kg',
    'Dolomite': 'dolomite_kg',
    'Albite': 'albite_kg',
    'Anorthite': 'anorthite_kg',
    'Quartz': 'quartz_kg',
}


@lru_cache(maxsize=8)
def get_database(database=DEFAULT_DATABASE):
    return rkt.SupcrtDatabase(database)


def reaktoro_species_name(component_or_species):
    return COMPONENT_SPECIES.get(component_or_species, component_or_species)


@lru_cache(maxsize=256)
def get_species(component_or_species, database=DEFAULT_DATABASE):
    return get_database(database).species(reaktoro_species_name(component_or_species))


def species_molar_mass(component_or_species, database=DEFAULT_DATABASE):
    return float(get_species(component_or_species, database).molarMass())


def component_molar_mass(component, database=DEFAULT_DATABASE):
    return species_molar_mass(component, database)


def species_formula(component_or_species, database=DEFAULT_DATABASE):
    return get_species(component_or_species, database).formula().str()


def species_charge(component_or_species, database=DEFAULT_DATABASE):
    return float(get_species(component_or_species, database).charge())


def species_aggregate_state(component_or_species, database=DEFAULT_DATABASE):
    return str(get_species(component_or_species, database).aggregateState())


def mineral_density(component_or_phase, database=DEFAULT_DATABASE, temperature=298.15, pressure=1.0e5):
    species = get_species(component_or_phase, database)
    volume = float(species.props(float(temperature), float(pressure)).V0)
    if volume <= 0.0:
        raise ValueError(f'non-positive standard molar volume for {component_or_phase}')
    return float(species.molarMass()) / volume


DEFAULT_STATE = {
    'H2O': 1.0,
    'CO2(aq)': 8.801960000000e-4,
    'CO2(g)': 4.400980000000e-14,
    'Ca+2': 1.202307085205e-4,
    'Mg+2': 4.860780568036e-5,
    'Na+': 1.034514873904e-2,
    'K+': 3.909775142009e-5,
    'H+': 1.007391420091e-10,
    'OH-': 1.700788857991e-9,
    'Cl-': 1.598941510954e-2,
    'HCO3-': 3.050884428995e-4,
    'SO4-2': 9.606469715982e-5,
    'Al+3': 2.697989326027e-10,
    'SiO2(aq)': 1.802529000000e-5,
    'Calcite': 1.000872000000e-4,
    'Magnesite': 4.215710000000e-5,
    'Dolomite': 9.220070000000e-5,
    'Albite': 2.622230070000e-4,
    'Anorthite': 2.782072780000e-4,
    'Quartz': 6.008430000000e-5,
    'pH': 7.0,
}

SCENES = {
    'permafrost': dict(
        surface_area=5.0e-4,
        state={
            'CO2(aq)': 5.281176000000e-4,
            'Ca+2': 8.015380568036e-5,
            'Mg+2': 2.430390284018e-5,
            'Na+': 5.747304855023e-3,
            'Cl-': 9.040578387877e-3,
            'HCO3-': 1.830530657397e-4,
            'SiO2(aq)': 9.012645000000e-6}),
    'seabed': dict(
        surface_area=8.0e-4,
        state={
            'CO2(aq)': 7.921764000000e-4,
            'Ca+2': 4.007690284018e-4,
            'Mg+2': 1.263802947689e-3,
            'Na+': 1.080493312744e-2,
            'K+': 3.909775142009e-4,
            'Cl-': 1.949928671895e-2,
            'SO4-2': 2.689811520475e-3}),
    'saline_aquifer': dict(
        surface_area=1.0e-3,
        state={
            'CO2(aq)': 8.801960000000e-4,
            'Ca+2': 1.202307085205e-4,
            'Mg+2': 4.860780568036e-5,
            'Na+': 1.034514873904e-2,
            'Cl-': 1.598941510954e-2,
            'HCO3-': 3.050884428995e-4}),
    'basalt': dict(
        surface_area=2.0e-3,
        state={
            'CO2(aq)': 1.320294000000e-3,
            'Ca+2': 4.007690284018e-5,
            'Mg+2': 9.721561136073e-5,
            'Na+': 2.758706330411e-3,
            'K+': 1.954887571005e-5,
            'Cl-': 4.608922315388e-3,
            'SiO2(aq)': 4.806744000000e-5,
            'Al+3': 1.348994663014e-9,
            'Albite': 5.244460140000e-4,
            'Anorthite': 8.346218340000e-4,
            'Quartz': 3.004215000000e-5}),
}


def scene_state(scene=DEFAULT_SCENE):
    state = dict(DEFAULT_STATE)
    state.update(SCENES[scene]['state'])
    return state


def scene_config(scene=DEFAULT_SCENE, database=None, surface_area=None):
    if scene not in SCENES:
        raise ValueError(f'unknown mineralization scene: {scene}')
    cfg = ReactorConfig(
        scene=scene,
        database=DEFAULT_DATABASE if database is None else str(database),
        surface_area=float(SCENES[scene]['surface_area']))
    if surface_area is not None:
        cfg = replace(cfg, surface_area=float(surface_area))
    return cfg


def validate_species(database=DEFAULT_DATABASE):
    missing = []
    for name in COMPONENT_SPECIES:
        try:
            get_species(name, database)
        except Exception:
            missing.append((name, COMPONENT_SPECIES[name]))
    if missing:
        text = ', '.join(f'{name}->{species}' for name, species in missing)
        raise ValueError(f'species not found in Reaktoro database {database}: {text}')
    return True
