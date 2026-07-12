"""Gas-aqueous UV equilibrium solved with Reaktoro."""

import numpy as np
import reaktoro as rtk


class GasAqueousUVEquilibrium:
    """Equilibrate H2O and selected gases at fixed volume and energy."""

    def __init__(self, gas_names=None):
        gas_names = gas_names or ["CH4", "N2", "He"]
        gas_species = ["H2O(g)", *(f"{name}(g)" for name in gas_names)]
        aqueous_species = ["H2O(aq)", *(f"{name}(aq)" for name in gas_names)]
        self.names = gas_species + aqueous_species

        database = rtk.SupcrtDatabase("supcrtbl-organics")
        gas = rtk.GaseousPhase(" ".join(gas_species))
        aqueous = rtk.AqueousPhase(" ".join(aqueous_species))
        self.system = rtk.ChemicalSystem(database, gas, aqueous)
        self.system_names = [species.name() for species in self.system.species()]
        self.molar_mass = {
            species.name(): float(species.molarMass())
            for species in self.system.species()
        }

        specs = rtk.EquilibriumSpecs(self.system)
        specs.volume()
        specs.internalEnergy()
        self.solver = rtk.EquilibriumSolver(specs)
        options = rtk.EquilibriumOptions()
        options.epsilon = 1.0e-30
        self.solver.setOptions(options)

        self.conditions = rtk.EquilibriumConditions(specs)
        self.conditions.setLowerBoundTemperature(273.15, "K")
        self.conditions.setUpperBoundTemperature(1273.0, "K")
        self.conditions.setLowerBoundPressure(0.1, "MPa")
        self.conditions.setUpperBoundPressure(400.0, "MPa")

        self.state = rtk.ChemicalState(self.system)
        self.props = rtk.ChemicalProps(self.state)
        self.last_temperature = None
        self.last_pressure = None

    def solve(self, temperature, pressure, masses):
        is_mapping = isinstance(masses, dict)
        values = (
            [float(masses.get(name, 0.0)) for name in self.names]
            if is_mapping
            else [float(value) for value in masses]
        )
        if len(values) != len(self.names):
            raise ValueError(f"Expected {len(self.names)} species masses, got {len(values)}")

        mass_by_name = dict(zip(self.names, values))
        amounts = np.asarray([
            max(mass_by_name.get(name, 0.0), 1.0e-30) / self.molar_mass[name]
            for name in self.system_names
        ])
        self.state.temperature(float(temperature), "K")
        self.state.pressure(float(pressure), "Pa")
        self.state.setSpeciesAmounts(amounts)
        self.props.update(self.state)
        self.conditions.volume(self.props.volume())
        self.conditions.internalEnergy(self.props.internalEnergy())

        if self.solver.solve(self.state, self.conditions).failed():
            return None

        self.last_temperature = float(self.state.temperature())
        self.last_pressure = float(self.state.pressure())
        result = np.array([float(self.state.speciesMass(name)) for name in self.names])
        phase_size = len(self.names) // 2
        values = np.maximum(values, 0.0)
        totals = values[:phase_size] + values[phase_size:]
        solved_totals = result[:phase_size] + result[phase_size:]
        gas = np.divide(
            totals * result[:phase_size], solved_totals,
            out=np.zeros(phase_size), where=solved_totals > 0.0,
        )
        result = np.concatenate((gas, totals - gas)).tolist()
        return dict(zip(self.names, result)) if is_mapping else result

    def get_next_state(self, temperature, pressure, masses):
        return self.solve(temperature, pressure, masses)

    def get_temperature(self):
        return float(self.state.temperature())

    def get_pressure(self):
        return float(self.state.pressure())
