"""Generate Reaktoro gas-aqueous UV equilibrium training data."""

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import local
from time import perf_counter

import numpy as np


DEFAULT_SAMPLE_COUNT = 10000
DEFAULT_SEED = 20260709
DEFAULT_WORKERS = 4
TEMPERATURE_RANGE_K = (273.15, 573.0)
PRESSURE_RANGE_MPA = (1.0, 200.0)
EQUILIBRIUM_TEMPERATURE_RANGE_K = (273.15, 1273.0)
EQUILIBRIUM_PRESSURE_RANGE_MPA = (0.1, 400.0)
SPECIES_NAMES = (
    "H2O(g)", "CH4(g)", "N2(g)", "He(g)",
    "H2O(aq)", "CH4(aq)", "N2(aq)", "He(aq)",
)
COMPONENT_SPECIES = {
    "H2O": ("H2O(g)", "H2O(aq)"),
    "CH4": ("CH4(g)", "CH4(aq)"),
    "N2": ("N2(g)", "N2(aq)"),
    "He": ("He(g)", "He(aq)"),
}
MASS_RANGES_KG = {
    "H2O(g)": (1.0e-12, 1.0e-2), "CH4(g)": (1.0e-8, 1.0e1),
    "N2(g)": (1.0e-9, 3.0), "He(g)": (1.0e-12, 1.0e-2),
    "H2O(aq)": (1.0, 1.0e3), "CH4(aq)": (1.0e-10, 5.0e-1),
    "N2(aq)": (1.0e-11, 2.0e-1), "He(aq)": (1.0e-13, 1.0e-3),
}
REGIME_WEIGHTS = {
    "aqueous_dominated": 0.45, "mixed_transition": 0.35, "gas_dominated": 0.20,
}
REGIME_MASS_RANGES_KG = {
    "aqueous_dominated": {
        "H2O(g)": (1.0e-12, 1.0e-5), "CH4(g)": (1.0e-8, 1.0e-2),
        "N2(g)": (1.0e-9, 1.0e-3), "He(g)": (1.0e-12, 1.0e-6),
        "H2O(aq)": (1.0e1, 1.0e3), "CH4(aq)": (1.0e-8, 5.0e-1),
        "N2(aq)": (1.0e-9, 2.0e-1), "He(aq)": (1.0e-12, 1.0e-3),
    },
    "mixed_transition": {
        "H2O(g)": (1.0e-10, 1.0e-4), "CH4(g)": (1.0e-5, 1.0),
        "N2(g)": (1.0e-6, 1.0e-1), "He(g)": (1.0e-11, 1.0e-4),
        "H2O(aq)": (1.0, 1.0e3), "CH4(aq)": (1.0e-7, 1.0e-1),
        "N2(aq)": (1.0e-8, 1.0e-2), "He(aq)": (1.0e-12, 1.0e-4),
    },
    "gas_dominated": {
        "H2O(g)": (1.0e-8, 1.0e-2), "CH4(g)": (1.0e-3, 1.0e1),
        "N2(g)": (1.0e-5, 3.0), "He(g)": (1.0e-9, 1.0e-2),
        "H2O(aq)": (1.0, 3.0e2), "CH4(aq)": (1.0e-10, 1.0e-2),
        "N2(aq)": (1.0e-11, 1.0e-3), "He(aq)": (1.0e-13, 1.0e-5),
    },
}
SPLIT_FRACTIONS = {"train": 0.80, "val": 0.10, "test": 0.10}
FEATURE_NAMES = ("input_temperature_K", "input_pressure_Pa") + tuple(
    f"input_{name}_kg" for name in SPECIES_NAMES
)
TARGET_NAMES = ("equilibrium_temperature_K", "equilibrium_pressure_Pa") + tuple(
    f"equilibrium_{name}_kg" for name in SPECIES_NAMES
)
ROW_FIELDS = (
    "sample_id", "sampling_regime", "split", *FEATURE_NAMES,
    "input_pressure_MPa", *TARGET_NAMES, "equilibrium_pressure_MPa",
    "solve_elapsed_s",
)


@dataclass(frozen=True)
class InputSamples:
    temperature_K: np.ndarray
    pressure_Pa: np.ndarray
    masses_kg: np.ndarray
    regimes: np.ndarray = None

    def __len__(self):
        return len(self.temperature_K)


def _latin_hypercube(count, dimensions, rng):
    base = (np.arange(count) + rng.random(count)) / count
    return np.column_stack([rng.permutation(base) for _ in range(dimensions)])


def _regimes(count, rng):
    names = np.array(list(REGIME_WEIGHTS))
    weights = np.array(list(REGIME_WEIGHTS.values()))
    counts = np.floor(weights * count).astype(int)
    counts[np.argsort(weights * count - counts)[::-1][:count - counts.sum()]] += 1
    values = np.repeat(names, counts)
    rng.shuffle(values)
    return values


def sample_inputs(count, seed=DEFAULT_SEED):
    if count <= 0:
        raise ValueError("count must be positive")
    rng = np.random.default_rng(seed)
    cube = _latin_hypercube(count, len(SPECIES_NAMES) + 2, rng)
    regimes = _regimes(count, rng)
    temperature = TEMPERATURE_RANGE_K[0] + cube[:, 0] * np.ptp(TEMPERATURE_RANGE_K)
    pressure = PRESSURE_RANGE_MPA[0] + cube[:, 1] * np.ptp(PRESSURE_RANGE_MPA)
    masses = np.empty((count, len(SPECIES_NAMES)))
    for regime, ranges in REGIME_MASS_RANGES_KG.items():
        mask = regimes == regime
        for column, name in enumerate(SPECIES_NAMES):
            lo, hi = np.log10(ranges[name])
            masses[mask, column] = 10 ** (lo + cube[mask, column + 2] * (hi - lo))
    return InputSamples(temperature, pressure * 1.0e6, masses, regimes)


def _solver_factory():
    import reaktoro as rtk
    from zmlx.scen.uv_equilibrium.gas_aq_uv_equilibrium import GasAqueousUVEquilibrium
    rtk.Warnings.disable(906)
    return GasAqueousUVEquilibrium()


def _make_row(index, samples, solver, result, elapsed, offset):
    regime = "unspecified" if samples.regimes is None else str(samples.regimes[index])
    row = {
        "sample_id": float(offset + index), "sampling_regime": regime, "split": "",
        "input_temperature_K": float(samples.temperature_K[index]),
        "input_pressure_Pa": float(samples.pressure_Pa[index]),
        "input_pressure_MPa": float(samples.pressure_Pa[index]) / 1.0e6,
        "equilibrium_temperature_K": float(solver.last_temperature),
        "equilibrium_pressure_Pa": float(solver.last_pressure),
        "equilibrium_pressure_MPa": float(solver.last_pressure) / 1.0e6,
        "solve_elapsed_s": float(elapsed),
    }
    row.update(zip((f"input_{name}_kg" for name in SPECIES_NAMES), samples.masses_kg[index]))
    row.update(zip((f"equilibrium_{name}_kg" for name in SPECIES_NAMES), result))
    return row


def validate_row(row, relative_tolerance=1.0e-6, absolute_tolerance=1.0e-9):
    if not all(np.isfinite(float(row[name])) for name in (*FEATURE_NAMES, *TARGET_NAMES, "solve_elapsed_s")):
        return False, "nonfinite"
    for component, names in COMPONENT_SPECIES.items():
        before = sum(float(row[f"input_{name}_kg"]) for name in names)
        after = sum(float(row[f"equilibrium_{name}_kg"]) for name in names)
        if abs(after - before) > max(absolute_tolerance, relative_tolerance * before):
            return False, f"mass_conservation_{component}"
    return True, "ok"


def solve_inputs(samples, solver_factory=None, workers=1, sample_offset=0):
    factory = solver_factory or _solver_factory
    state = local()

    def solve(index):
        if not hasattr(state, "solver"):
            state.solver = factory()
        started = perf_counter()
        result = state.solver.solve(
            samples.temperature_K[index], samples.pressure_Pa[index],
            samples.masses_kg[index],
        )
        if result is None:
            return None
        row = _make_row(
            index, samples, state.solver, result, perf_counter() - started,
            sample_offset,
        )
        return row if validate_row(row)[0] else None

    if workers == 1:
        solved = [solve(index) for index in range(len(samples))]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            solved = list(pool.map(solve, range(len(samples))))
    return [row for row in solved if row is not None], sum(row is None for row in solved)


def assign_splits(rows, seed=DEFAULT_SEED):
    rows = [dict(row) for row in rows]
    order = np.random.default_rng(seed).permutation(len(rows))
    n_train = round(len(rows) * SPLIT_FRACTIONS["train"])
    n_val = round(len(rows) * SPLIT_FRACTIONS["val"])
    labels = np.full(len(rows), "test", dtype=object)
    labels[order[:n_train]] = "train"
    labels[order[n_train:n_train + n_val]] = "val"
    for row, label in zip(rows, labels):
        row["split"] = label
    return rows


def rows_to_arrays(rows):
    splits = np.array([row.get("split", "") for row in rows])
    return {
        "x": np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=float),
        "y": np.array([[row[name] for name in TARGET_NAMES] for row in rows], dtype=float),
        "feature_names": np.array(FEATURE_NAMES), "target_names": np.array(TARGET_NAMES),
        "species_names": np.array(SPECIES_NAMES), "split": splits,
        "train_indices": np.flatnonzero(splits == "train"),
        "val_indices": np.flatnonzero(splits == "val"),
        "test_indices": np.flatnonzero(splits == "test"),
    }


def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=ROW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_npz(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **rows_to_arrays(rows))


def write_metadata(path, rows, failures, seed, requested_samples, attempts, workers,
                   elapsed_s, **_):
    metadata = {
        "requested_samples": requested_samples, "successful_samples": len(rows),
        "failed_solves": failures, "attempted_samples": attempts, "seed": seed,
        "workers": workers, "elapsed_s": elapsed_s,
        "temperature_range_K": TEMPERATURE_RANGE_K,
        "pressure_range_MPa": PRESSURE_RANGE_MPA,
        "species_names": SPECIES_NAMES, "mass_ranges_kg": MASS_RANGES_KG,
        "split_counts": {
            name: sum(row.get("split") == name for row in rows)
            for name in SPLIT_FRACTIONS
        },
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def generate_dataset(count=DEFAULT_SAMPLE_COUNT, seed=DEFAULT_SEED,
                     workers=DEFAULT_WORKERS, max_attempts=None):
    max_attempts = max_attempts or count * 3
    rows, failures, attempts = [], 0, 0
    while len(rows) < count and attempts < max_attempts:
        size = min(1000, count - len(rows), max_attempts - attempts)
        solved, failed = solve_inputs(
            sample_inputs(size, seed + attempts), workers=workers,
            sample_offset=attempts,
        )
        rows.extend(solved)
        failures += failed
        attempts += size
    return rows[:count], failures, attempts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--max-attempts", type=int)
    parser.add_argument(
        "--out-dir", type=Path,
        default=Path(__file__).parent / "data" / "gas_aq_uv_equilibrium",
    )
    parser.add_argument("--prefix")
    args = parser.parse_args(argv)

    started = perf_counter()
    rows, failures, attempts = generate_dataset(
        args.samples, args.seed, args.workers, args.max_attempts
    )
    if len(rows) != args.samples:
        raise RuntimeError(f"Generated {len(rows)} of {args.samples} samples")
    rows = assign_splits(rows, args.seed)
    prefix = args.prefix or f"gas_aq_uv_equilibrium_{args.samples}_seed{args.seed}"
    csv_path = args.out_dir / f"{prefix}.csv"
    npz_path = args.out_dir / f"{prefix}.npz"
    write_csv(rows, csv_path)
    write_npz(rows, npz_path)
    write_metadata(
        args.out_dir / f"{prefix}.metadata.json", rows, failures, args.seed,
        args.samples, attempts, args.workers, perf_counter() - started,
    )
    print(csv_path)
    print(npz_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
