"""Gas-aqueous migration with batched PyTorch/Reaktoro equilibrium."""

from concurrent.futures import ThreadPoolExecutor
from os import cpu_count, environ
from pathlib import Path
from threading import local

import numpy as np

from zmlx import *
from zmlx.scen.uv_equilibrium.generate_gas_aq_uv_dataset import SPECIES_NAMES


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / (
    "gas_aq_uv_surrogate_augmented_round5_scale_invariant_h256"
) / "gas_aq_uv_surrogate_h256_e1000.pt"
BACKEND_ENV = "GAS_AQ_BALANCE_BACKEND"
MODEL_ENV = "GAS_AQ_SURROGATE_MODEL"
ANCHOR_ENV = "GAS_AQ_REAKTORO_ANCHOR_INTERVAL"
DEFAULT_BACKEND = "hybrid"
DEFAULT_ANCHOR_INTERVAL = 25
DOMAIN_LIMITS = np.array((3.0e3, 2.0e2, 5.0, 20.0)) * 1.05

_pool = ThreadPoolExecutor(max_workers=cpu_count() or 1)
_rtk_local = local()
_surrogate = None
_calls = {}
_initial_mass = {}


def _get_surrogate():
    global _surrogate
    if _surrogate is None:
        import torch
        from zmlx.scen.uv_equilibrium.train_gas_aq_uv_surrogate import (
            GasAqueousUVSurrogate,
        )
        torch.set_num_threads(1)
        path = Path(environ.get(MODEL_ENV, MODEL_PATH))
        if not path.exists():
            raise FileNotFoundError(path)
        _surrogate = GasAqueousUVSurrogate.from_checkpoint(path)
    return _surrogate


def _get_reaktoro():
    if not hasattr(_rtk_local, "solver"):
        from zmlx.scen.uv_equilibrium.gas_aq_uv_equilibrium import (
            GasAqueousUVEquilibrium,
        )
        _rtk_local.solver = GasAqueousUVEquilibrium()
    return _rtk_local.solver


def _solve_reaktoro(args):
    index, temperature, pressure, masses = args
    solver = _get_reaktoro()
    result = solver.solve(temperature, pressure, masses)
    value = solver.last_temperature if result is not None else temperature
    return index, value, result


def _domain_mask(temperature, pressure, masses):
    totals = np.maximum(masses[:, :4], 0.0) + np.maximum(masses[:, 4:], 0.0)
    return (
        (temperature >= 273.15) & (temperature <= 800.0)
        & (pressure >= 1.0e6) & (pressure <= 200.0e6)
        & np.all(totals <= DOMAIN_LIMITS, axis=1)
    )


def _conserve(before, predicted):
    totals = np.maximum(before[:, :4], 0.0) + np.maximum(before[:, 4:], 0.0)
    safe = np.where(np.isfinite(predicted) & (predicted > 0.0), predicted, 0.0)
    predicted_totals = safe[:, :4] + safe[:, 4:]
    fraction = np.divide(
        safe[:, :4], predicted_totals,
        out=np.zeros_like(totals), where=predicted_totals > 0.0,
    )
    gas = totals * fraction
    corrected = np.concatenate((gas, totals - gas), axis=1)
    raw_error = np.abs(predicted_totals - totals) / np.maximum(totals, 1.0e-30)
    return corrected, float(np.max(raw_error)) if raw_error.size else 0.0


def _solve_batch(temperature, pressure, masses, anchor):
    backend = environ.get(BACKEND_ENV, DEFAULT_BACKEND).lower()
    if backend not in ("surrogate", "hybrid", "reaktoro"):
        raise ValueError(f"Unsupported backend: {backend}")

    candidates = np.zeros(len(temperature), dtype=bool)
    if backend == "surrogate":
        candidates[:] = True
    elif backend == "hybrid" and not anchor:
        candidates = _domain_mask(temperature, pressure, masses)

    next_temperature = temperature.copy()
    predicted = masses.copy()
    solved = np.zeros(len(temperature), dtype=bool)
    if np.any(candidates):
        try:
            values = _get_surrogate().solve_batch(
                temperature[candidates], pressure[candidates], masses[candidates]
            )
            valid = (
                np.isfinite(values[0]) & np.isfinite(values[1])
                & np.all(np.isfinite(values[2]), axis=1)
            )
            if backend == "surrogate" and not np.all(valid):
                raise FloatingPointError("Surrogate returned nonfinite values")
            rows = np.flatnonzero(candidates)[valid]
            next_temperature[rows] = values[0][valid]
            predicted[rows] = values[2][valid]
            solved[rows] = True
        except Exception:
            if backend == "surrogate":
                raise
            print("Surrogate failed; using Reaktoro fallback", flush=True)

    rtk_rows = np.flatnonzero(~solved)
    failed = []
    arguments = (
        (row, temperature[row], pressure[row], masses[row]) for row in rtk_rows
    )
    for row, value, result in _pool.map(_solve_reaktoro, arguments):
        if result is None:
            failed.append(row)
        else:
            next_temperature[row] = value
            predicted[row] = result

    next_temperature = np.where(np.isfinite(next_temperature), next_temperature, temperature)
    corrected, error = _conserve(masses, predicted)
    if failed:
        corrected[failed] = masses[failed]
        print(f"Reaktoro warning cells: {len(failed)}/{len(rtk_rows)}", flush=True)
    return next_temperature, corrected, error


def _mass_matrix(mass):
    h2o, ch4aq, n2aq, heaq = (
        mass[name] for name in ("H2O", "CH4(aq)", "N2(aq)", "He(aq)")
    )
    ch4, n2, he = (mass[name] for name in ("CH4", "N2", "He"))
    return np.column_stack((np.zeros_like(h2o), ch4, n2, he, h2o, ch4aq, n2aq, heaq))


def _component_totals(masses):
    values = np.maximum(masses, 0.0)
    return (values[:, :4] + values[:, 4:]).sum(axis=0)


def _model_key(model):
    return str(model.handle_str)


def _reset_mass_report(model, masses):
    key = _model_key(model)
    _calls[key] = 0
    _initial_mass[key] = _component_totals(masses)
    _report_mass(model, masses, 0, 0.0)


def _report_mass(model, masses, call, error):
    if call % 25 and error <= 1.0e-10:
        return
    initial = _initial_mass.setdefault(_model_key(model), _component_totals(masses))
    current = _component_totals(masses)
    drift = np.abs(current - initial) / np.maximum(initial, 1.0e-30)
    values = ", ".join(
        f"{name}(initial={initial[i]:.6e}, current={current[i]:.6e}, "
        f"drift={drift[i]:.3e})"
        for i, name in enumerate(("H2O", "CH4", "N2", "He"))
    )
    print(f"mass conservation: {values}, local correction={error:.3e}", flush=True)


def create(jx, jz):
    mesh = create_cube(
        x=linspace(0, 300, jx + 1), y=(-0.5, 0.5), z=linspace(-500, 0, jz + 1)
    )
    gas = ch4.create()
    water = h2o.create()
    fluids = [
        FluDef.create(
            defs=[gas.get_copy("N2"), gas.get_copy("He"), gas.get_copy("CH4")],
            name="gas",
        ),
        FluDef.create(
            defs=[
                water.get_copy("H2O"), water.get_copy("N2(aq)"),
                water.get_copy("He(aq)"), water.get_copy("CH4(aq)"),
            ],
            name="aqueous",
        ),
    ]

    def temperature(_, __, z):
        return 300.15 - 0.0443 * z

    def pressure(_, __, z):
        return 15.0e6 - 1.0e4 * z

    def gas_region(x, y, z):
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def saturation(x, y, z):
        return {"CH4": 1} if gas_region(x, y, z) else {"H2O": 1, "He(aq)": 0.001}

    z_min, z_max = mesh.get_pos_range(2)

    def heat_capacity(_, __, z):
        return 1.0e20 if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1 else 1.0e6

    model = tfc.create(
        mesh, porosity=lambda x, y, z: 1.0 if gas_region(x, y, z) else 0.1,
        pore_modulus=100.0e6, denc=heat_capacity, dist=0.1,
        temperature=temperature, p=pressure, s=saturation, perm=1.0e-14,
        heat_cond=2.0, fludefs=fluids, dt_max=3600 * 24 * 30.0,
        gravity=(0, 0, -10),
    )
    model.set_text(key="solve", text={"time_max": 3600 * 24 * 365 * 6})
    step_iteration.add_setting(model, name="balance", step=1, args=["@model"])
    arrays = as_numpy(model)
    names = tfc.list_comp(model, keep_structure=False)
    _reset_mass_report(
        model, _mass_matrix({name: arrays.fluids(name).mass for name in names})
    )
    return model


def balance(model: Seepage):
    key = _model_key(model)
    call = _calls.get(key, 0) + 1
    _calls[key] = call
    arrays = as_numpy(model)
    pressure = arrays.cells.pre
    temperature = arrays.fluids("aqueous").get_attr("temperature")
    names = tfc.list_comp(model, keep_structure=False)
    mass = {name: arrays.fluids(name).mass for name in names}
    masses = _mass_matrix(mass)
    interval = int(environ.get(ANCHOR_ENV, DEFAULT_ANCHOR_INTERVAL))
    anchor = environ.get(BACKEND_ENV, DEFAULT_BACKEND).lower() == "hybrid" and (
        call == 1 or (interval > 0 and call % interval == 0)
    )
    temperature[:], result, error = _solve_batch(temperature, pressure, masses, anchor)
    mass["H2O"][:] = result[:, 0] + result[:, 4]
    mass["CH4"][:], mass["N2"][:], mass["He"][:] = result[:, 1:4].T
    mass["CH4(aq)"][:], mass["N2(aq)"][:], mass["He(aq)"][:] = result[:, 5:8].T
    arrays.fluids("aqueous").set_attr("temperature", temperature)
    for name in names:
        arrays.fluids(name).mass = mass[name]
    _report_mass(model, result, call, error)


def show(model, jx, jz):
    def draw(figure):
        from zmlx.plt import AutoLayout
        layout = AutoLayout(
            figure, num_plots=6, subplot_aspect_ratio=0.6,
            aspect="equal", xlabel="x/m", ylabel="z/m",
        )
        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        angles = np.linspace(0, np.pi, 100)
        axis = layout.add_axes2(
            add_contourf, x, z, tfc.get_p(model, shape=(jx, jz)),
            cbar=dict(label="p", shrink=0.6), title="pressure", cmap="coolwarm",
        )
        axis.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), "k--")
        gas_volume = tfc.get_v(model, fid="gas", shape=(jx, jz))
        water_volume = tfc.get_v(model, fid="aqueous", shape=(jx, jz))
        axis = layout.add_axes2(
            add_contourf, x, z, gas_volume / (gas_volume + water_volume),
            cbar=dict(label="s", shrink=0.6), title="gas saturation",
        )
        axis.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), "r--")
        for name in ("CH4", "He"):
            for fluid in (name, f"{name}(aq)"):
                values = tfc.get_m(model, fid=fluid, shape=(jx, jz))
                values = np.log10(1.0 + values / max(values.max() * 1.0e-6, 1.0e-30))
                layout.add_axes2(
                    add_contourf, x, z, values,
                    cbar=dict(label="log mass", shrink=0.6), title=f"{fluid} mass",
                )

    return plot(
        draw, caption=f"Seepage({model.handle_str})",
        suptitle=f"time: {tfc.get_time(model, as_str=True)}",
        tight_layout=True, clear=True, gui_mode=True,
    )


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(
        model, close_after_done=False,
        extra_plot=lambda: show(model, jx, jz), slots={"balance": balance},
    )


if __name__ == "__main__":
    gui.execute(main, close_after_done=False)
