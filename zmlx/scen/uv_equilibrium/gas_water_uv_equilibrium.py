# -*- coding: utf-8 -*-

import csv
from functools import lru_cache
import os
from pathlib import Path

import numpy as np
from reaktoro import *


COMPONENTS = ("He", "N2", "CH4")
FAILURE_LOG = Path(__file__).with_name("reaktoro_failed_cells.csv")

try:
    Warnings.enable(906)
except Exception:
    pass


class GasWaterUVEquilibrium:
    def __init__(
            self, database_name="supcrtbl", gas_components=COMPONENTS,
            include_water_vapor=True, epsilon=1.0e-30, auto_use_organics=True):
        self.requested_database_name = database_name
        self.gas_components = tuple(gas_components)
        errors = {}
        candidates = [database_name]
        if auto_use_organics and database_name == "supcrtbl":
            candidates.append("supcrtbl-organics")
        for name in candidates:
            try:
                self._build(name, include_water_vapor, epsilon)
                self.database_used = name
                self.fallback_errors = errors
                return
            except Exception as err:
                errors[name] = str(err)
        raise RuntimeError(f"GasWaterUVEquilibrium 初始化失败: {errors}")

    def _build(self, database_name, include_water_vapor, epsilon):
        self.db = SupcrtDatabase(database_name)
        self.water_aq = "H2O(aq)"
        self.gas_species = {name: f"{name}(g)" for name in self.gas_components}
        self.aq_gas_species = {name: f"{name}(aq)" for name in self.gas_components}

        gas_names = list(self.gas_species.values())
        if include_water_vapor:
            gas_names.insert(0, "H2O(g)")
        aqueous = AqueousPhase(" ".join([self.water_aq, *self.aq_gas_species.values()]))
        gases = GaseousPhase(" ".join(gas_names))

        self.system = ChemicalSystem(self.db, gases, aqueous)
        specs = EquilibriumSpecs(self.system)
        specs.volume()
        specs.internalEnergy()
        self.solver = EquilibriumSolver(specs)
        specs_tp = EquilibriumSpecs(self.system)
        specs_tp.temperature()
        specs_tp.pressure()
        self.solver_tp = EquilibriumSolver(specs_tp)
        if epsilon is not None:
            opts = EquilibriumOptions()
            opts.epsilon = epsilon
            self.solver.setOptions(opts)
            self.solver_tp.setOptions(opts)
        self.specs = specs
        self.specs_tp = specs_tp
        self.species_names = [sp.name() for sp in self.system.species()]
        self.species_index = {name: i for i, name in enumerate(self.species_names)}
        self.molar_mass = {sp.name(): float(sp.molarMass()) for sp in self.system.species()}

    def solve(
            self, temperature_K, pressure_Pa, water_kg,
            aq_gas_kg=None, gas_kg=None, fixed_volume_m3=None,
            temperature_bounds_K=(250.0, 500.0), pressure_bounds_Pa=(1.0e5, 1.0e8)):
        aq_gas_kg = aq_gas_kg or {}
        gas_kg = gas_kg or {}

        state0 = ChemicalState(self.system)
        state0.temperature(float(temperature_K), "K")
        state0.pressure(float(pressure_Pa), "Pa")
        self._set_kg(state0, self.water_aq, water_kg)
        for name in self.gas_components:
            self._set_kg(state0, self.gas_species[name], gas_kg.get(name, 0.0))
            self._set_kg(state0, self.aq_gas_species[name], aq_gas_kg.get(name, 0.0))

        props0 = ChemicalProps(state0)
        volume0 = float(props0.volume()) if fixed_volume_m3 is None else float(fixed_volume_m3)
        energy0 = float(props0.internalEnergy())

        conditions = EquilibriumConditions(self.specs)
        conditions.volume(volume0)
        conditions.internalEnergy(energy0)
        conditions.setLowerBoundTemperature(float(temperature_bounds_K[0]), "K")
        conditions.setUpperBoundTemperature(float(temperature_bounds_K[1]), "K")
        conditions.setLowerBoundPressure(float(pressure_bounds_Pa[0]), "Pa")
        conditions.setUpperBoundPressure(float(pressure_bounds_Pa[1]), "Pa")

        state = ChemicalState(state0)
        uv_success = True
        uv_error = ""
        try:
            result = self.solver.solve(state, conditions)
            if hasattr(result, "succeeded") and not result.succeeded():
                raise RuntimeError("Reaktoro equilibrium solver did not converge")
        except Exception as err:
            uv_success = False
            uv_error = str(err)
            return {"success": False, "error": uv_error, "uv_success": False, "uv_error": uv_error}

        props = ChemicalProps(state)
        all_kg = self.species_masses(state)
        return {
            "success": True,
            "error": "" if uv_success else f"UV failed; fallback success: {uv_error}",
            "uv_success": uv_success,
            "uv_error": uv_error,
            "database_requested": self.requested_database_name,
            "database_used": self.database_used,
            "temperature_K": float(state.temperature()),
            "pressure_Pa": float(state.pressure()),
            "water_kg": all_kg.get(self.water_aq, 0.0),
            "gas_kg": {name: all_kg.get(self.gas_species[name], 0.0) for name in self.gas_components},
            "aq_gas_kg": {name: all_kg.get(self.aq_gas_species[name], 0.0) for name in self.gas_components},
            "all_species_kg": all_kg,
            "diagnostics": {
                "V0_m3": volume0,
                "U0_J": energy0,
                "V_final_m3": float(props.volume()),
                "U_final_J": float(props.internalEnergy()),
                "volume_error_m3": float(props.volume()) - volume0,
                "internal_energy_error_J": float(props.internalEnergy()) - energy0,
            },
        }

    def react(self, p, t, mass, components=None, failure_log=FAILURE_LOG):
        components = tuple(components or self.gas_components)
        gas_mass = sum(mass[name] for name in components)
        for i in np.flatnonzero((mass["H2O"] > 1.0e-20) & (gas_mass > 1.0e-6 * mass["H2O"])):
            gas_kg = {name: float(mass[name][i]) for name in components}
            aq_gas_kg = {name: float(mass[f"{name}(aq)"][i]) for name in components}
            result = self.solve(
                temperature_K=float(t[i]),
                pressure_Pa=float(p[i]),
                water_kg=float(mass["H2O"][i]),
                aq_gas_kg=aq_gas_kg,
                gas_kg=gas_kg,
            )
            if not result["success"] or not result.get("uv_success", True):
                self._record_failure(failure_log, i, p, t, mass, gas_kg, aq_gas_kg, result, components)
            if not result["success"]:
                continue
            for name in components:
                total0 = gas_kg[name] + aq_gas_kg[name]
                total_eq = result["gas_kg"][name] + result["aq_gas_kg"][name]
                if total_eq > 0.0:
                    mass[name][i] = total0 * result["gas_kg"][name] / total_eq
                    mass[f"{name}(aq)"][i] = total0 * result["aq_gas_kg"][name] / total_eq

    def _record_failure(self, failure_log, i, p, t, mass, gas_kg, aq_gas_kg, result, components):
        if failure_log is None:
            return
        count = getattr(self, "failure_count", 0) + 1
        self.failure_count = count
        path = Path(failure_log)
        if not getattr(self, "_failure_log_started", False):
            self._failure_log_started = True
            print(f"Reaktoro未收敛输入将记录到: {path}")
        row = {
            "failure_no": count,
            "cell_index": int(i),
            "temperature_K": float(t[i]),
            "pressure_Pa": float(p[i]),
            "water_kg": float(mass["H2O"][i]),
            "gas_total_kg": float(sum(gas_kg.values())),
            "gas_water_ratio": float(sum(gas_kg.values()) / mass["H2O"][i]),
            "error": result.get("error", ""),
        }
        for name in components:
            row[f"gas_{name}_kg"] = gas_kg[name]
            row[f"aq_{name}_kg"] = aq_gas_kg[name]
        path = _append_csv_row(path, row)
        print(
            f"Reaktoro cell {int(i)} recorded: "
            f"T={float(t[i]):.6g} K, P={float(p[i]):.6g} Pa, "
            f"water={float(mass['H2O'][i]):.6g} kg, "
            f"gas_total={float(sum(gas_kg.values())):.6g} kg, "
            f"gas/water={float(sum(gas_kg.values()) / mass['H2O'][i]):.6g}, "
            f"csv={path}, "
            f"error={result.get('error', '')}"
        )

    def species_masses(self, state):
        return {name: self._get_mol(state, name) * self.molar_mass[name] for name in self.species_names}

    def describe(self):
        return {
            "database_requested": self.requested_database_name,
            "database_used": self.database_used,
            "gas_components": self.gas_components,
            "aqueous_species_map": dict(self.aq_gas_species),
            "gas_species_map": dict(self.gas_species),
            "fallback_errors": dict(getattr(self, "fallback_errors", {})),
        }

    def _set_kg(self, state, species, mass_kg):
        if mass_kg and float(mass_kg) > 0.0:
            state.set(species, float(mass_kg) / self.molar_mass[species], "mol")

    def _get_mol(self, state, species):
        try:
            return float(state.speciesAmount(species))
        except Exception:
            amounts = state.speciesAmounts()
            if hasattr(amounts, "asarray"):
                amounts = amounts.asarray()
            return float(amounts[self.species_index[species]])


@lru_cache(maxsize=4)
def _equilibrium(components):
    return GasWaterUVEquilibrium(
        database_name="supcrtbl",
        gas_components=tuple(components),
        include_water_vapor=False,
        auto_use_organics=True,
    )


def _append_csv_row(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _write_csv_row(path, row)
        return path
    except PermissionError:
        path = path.with_name(f"{path.stem}_{os.getpid()}{path.suffix}")
        _write_csv_row(path, row)
        return path


def _write_csv_row(path, row):
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)

def react_gas_water(p, t, mass, components=COMPONENTS, failure_log=FAILURE_LOG):
    _equilibrium(tuple(components)).react(p, t, mass, components=components, failure_log=failure_log)
