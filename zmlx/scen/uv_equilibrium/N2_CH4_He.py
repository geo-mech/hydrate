# -*- coding: utf-8 -*-

import reaktoro as rtk

class GasWaterUVEquilibrium:
    def __init__(self):
        db = rtk.SupcrtDatabase("supcrtbl-organics")

        aqueous = rtk.AqueousPhase("H2O(aq) CH4(aq) N2(aq) He(aq)")
        gases = rtk.GaseousPhase("H2O(g) CH4(g) N2(g) He(g)")
        self.names = ['H2O(aq)', 'CH4(aq)', 'N2(aq)', 'He(aq)', 'H2O(g)', 'CH4(g)', 'N2(g)', 'He(g)']
        self.system = rtk.ChemicalSystem(db, gases, aqueous)
        self.molar_mass = {sp.name(): float(sp.molarMass()) for sp in self.system.species()}

        self.specs = rtk.EquilibriumSpecs(self.system)
        # 有用
        self.specs.volume()
        self.specs.internalEnergy()
        self.solver = rtk.EquilibriumSolver(self.specs)
        opts = rtk.EquilibriumOptions()
        opts.epsilon = 1.0e-30
        self.solver.setOptions(opts)

        self.conditions = rtk.EquilibriumConditions(self.specs)
        self.conditions.setLowerBoundTemperature(275, "K")
        self.conditions.setUpperBoundTemperature(500.0, "K")
        self.conditions.setLowerBoundPressure(0.1, "MPa")
        self.conditions.setUpperBoundPressure(100.0, "MPa")

        self.state = rtk.ChemicalState(self.system)

    def get_next_state(self, temperature, pressure, masses):
        """
        单位是Pa、K和kg
        """
        assert isinstance(masses, dict)
        self.state.temperature(temperature, "K")
        self.state.pressure(pressure, "Pa")
        for name in self.names:
            m = masses.get(name, 0.0)
            m = max(1.0e-15, m)
            self.state.set(name, m, "kg")

        props0 = rtk.ChemicalProps(self.state)
        volume0 = props0.volume()
        energy0 = props0.internalEnergy()
        self.conditions.volume(volume0)
        self.conditions.internalEnergy(energy0)

        result = self.solver.solve(self.state, self.conditions)
        if hasattr(result, "succeeded") and not result.succeeded():
            raise RuntimeError("Reaktoro equilibrium solver did not converge")
        return {name: float(self.state.speciesAmount(name) * self.molar_mass[name]) for name in self.names}