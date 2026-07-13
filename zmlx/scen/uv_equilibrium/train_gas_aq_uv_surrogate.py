"""Train and run the scale-invariant PyTorch UV surrogate."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from zmlx.scen.uv_equilibrium.generate_gas_aq_uv_dataset import (
    DEFAULT_SAMPLE_COUNT as DATASET_SAMPLE_COUNT,
    DEFAULT_SEED as DATASET_SEED,
    EQUILIBRIUM_PRESSURE_RANGE_MPA,
    EQUILIBRIUM_TEMPERATURE_RANGE_K,
    PRESSURE_RANGE_MPA,
    SPECIES_NAMES,
    TEMPERATURE_RANGE_K,
)


DEFAULT_DATASET = Path(__file__).parent / "data" / "gas_aq_uv_equilibrium" / (
    f"gas_aq_uv_equilibrium_{DATASET_SAMPLE_COUNT}_seed{DATASET_SEED}.npz"
)
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "models" / (
    "gas_aq_uv_surrogate_augmented_round5_scale_invariant_h256"
)
DEFAULT_HIDDEN_SIZE = 256
DEFAULT_EPOCHS = 1000
DEFAULT_BATCH_SIZE = 1024
DEFAULT_LEARNING_RATE = 5.0e-4
DEFAULT_SEED = 20260710
FEATURE_TRANSFORM = "component_fractions_v2"
COMPONENT_FRACTION_RANGE = (1.0e-20, 1.0)
COMPONENT_PRESENCE_FRACTION = 1.0e-12
TARGET_NAMES = (
    "temperature", "pressure", "H2O_gas_fraction", "CH4_gas_fraction",
    "N2_gas_fraction", "He_gas_fraction",
)


class UVSurrogateNet(nn.Module):
    def __init__(self, input_size=10, hidden_size=DEFAULT_HIDDEN_SIZE, output_size=6):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, values):
        return self.layers(values)


@dataclass
class Dataset:
    x: torch.Tensor
    y: torch.Tensor
    weights: torch.Tensor
    train_indices: np.ndarray
    val_indices: np.ndarray
    test_indices: np.ndarray


def _scale(values, bounds):
    return (np.asarray(values, dtype=float) - bounds[0]) / (bounds[1] - bounds[0])


def _component_totals(masses):
    masses = np.maximum(np.asarray(masses, dtype=float), 0.0)
    return masses[..., :4] + masses[..., 4:]


def encode_inputs(temperature, pressure, masses):
    temperature = np.asarray(temperature, dtype=float).reshape(-1)
    pressure = np.asarray(pressure, dtype=float).reshape(-1)
    masses = np.asarray(masses, dtype=float).reshape(-1, 8)
    totals = _component_totals(masses)
    total_mass = totals.sum(axis=1, keepdims=True)
    fractions = np.divide(
        totals, total_mass, out=np.zeros_like(totals), where=total_mass > 0.0
    )
    gas_fractions = np.divide(
        np.maximum(masses[:, :4], 0.0), totals,
        out=np.zeros_like(totals), where=totals > 0.0,
    )
    lo, hi = np.log10(COMPONENT_FRACTION_RANGE)
    features = np.empty((len(masses), 10), dtype=np.float32)
    features[:, 0] = _scale(temperature, TEMPERATURE_RANGE_K)
    features[:, 1] = _scale(pressure / 1.0e6, PRESSURE_RANGE_MPA)
    features[:, 2::2] = (
        np.log10(np.maximum(fractions, COMPONENT_FRACTION_RANGE[0])) - lo
    ) / (hi - lo)
    features[:, 3::2] = gas_fractions
    return features


def _encode_targets(rows):
    rows = np.asarray(rows, dtype=float)
    totals = _component_totals(rows[:, 2:])
    gas_fractions = np.divide(
        np.maximum(rows[:, 2:6], 0.0), totals,
        out=np.zeros_like(totals), where=totals > 0.0,
    )
    return np.column_stack((
        _scale(rows[:, 0], EQUILIBRIUM_TEMPERATURE_RANGE_K),
        _scale(rows[:, 1] / 1.0e6, EQUILIBRIUM_PRESSURE_RANGE_MPA),
        gas_fractions,
    )).astype(np.float32)


def make_target_weights(x_raw):
    totals = _component_totals(np.asarray(x_raw, dtype=float)[:, 2:])
    total_mass = totals.sum(axis=1, keepdims=True)
    fractions = np.divide(
        totals, total_mass, out=np.zeros_like(totals), where=total_mass > 0.0
    )
    presence = fractions / (fractions + COMPONENT_PRESENCE_FRACTION)
    weights = np.empty((len(totals), 6), dtype=np.float32)
    weights[:, :2] = (1.0, 0.25)
    weights[:, 2:] = presence * np.array((0.5, 2.0, 1.0, 2.0))
    return weights


def load_dataset(path):
    data = np.load(path, allow_pickle=True)
    x_raw = np.asarray(data["x"], dtype=float)
    y_raw = np.asarray(data["y"], dtype=float)
    return Dataset(
        torch.tensor(encode_inputs(x_raw[:, 0], x_raw[:, 1], x_raw[:, 2:])),
        torch.tensor(_encode_targets(y_raw)),
        torch.tensor(make_target_weights(x_raw)),
        *(
            np.asarray(data[name], dtype=np.int64)
            for name in ("train_indices", "val_indices", "test_indices")
        ),
    )


def _loss(prediction, target, weights):
    return torch.sum((prediction - target) ** 2 * weights) / weights.sum().clamp(min=1.0)


@torch.no_grad()
def evaluate_loss(model, dataset, indices):
    model.eval()
    return float(_loss(model(dataset.x[indices]), dataset.y[indices], dataset.weights[indices]))


def train_model(dataset, hidden_size=DEFAULT_HIDDEN_SIZE, epochs=DEFAULT_EPOCHS,
                batch_size=DEFAULT_BATCH_SIZE, learning_rate=DEFAULT_LEARNING_RATE,
                seed=DEFAULT_SEED):
    torch.manual_seed(seed)
    model = UVSurrogateNet(dataset.x.shape[1], hidden_size, dataset.y.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loader = DataLoader(
        TensorDataset(
            dataset.x[dataset.train_indices], dataset.y[dataset.train_indices],
            dataset.weights[dataset.train_indices],
        ),
        batch_size=batch_size, shuffle=True,
    )
    history, best_loss, best_state = [], float("inf"), None
    for epoch in range(1, epochs + 1):
        model.train()
        for x, y, weights in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = _loss(model(x), y, weights)
            loss.backward()
            optimizer.step()
        if epoch == 1 or epoch % 25 == 0 or epoch == epochs:
            value = evaluate_loss(model, dataset, dataset.val_indices)
            history.append({"epoch": epoch, "val_mse": value})
            print(f"epoch={epoch} val_mse={value:.6e}", flush=True)
            if value < best_loss:
                best_loss = value
                best_state = {
                    name: tensor.detach().clone()
                    for name, tensor in model.state_dict().items()
                }
    if best_state:
        model.load_state_dict(best_state)
    return model, history


def _decode(prediction, masses):
    prediction = np.clip(np.asarray(prediction, dtype=float), 0.0, 1.0)
    totals = _component_totals(masses)
    gas = totals * prediction[:, 2:6]
    temperature = EQUILIBRIUM_TEMPERATURE_RANGE_K[0] + prediction[:, 0] * (
        EQUILIBRIUM_TEMPERATURE_RANGE_K[1] - EQUILIBRIUM_TEMPERATURE_RANGE_K[0]
    )
    pressure = EQUILIBRIUM_PRESSURE_RANGE_MPA[0] + prediction[:, 1] * (
        EQUILIBRIUM_PRESSURE_RANGE_MPA[1] - EQUILIBRIUM_PRESSURE_RANGE_MPA[0]
    )
    return temperature, pressure * 1.0e6, np.concatenate((gas, totals - gas), axis=1)


class GasAqueousUVSurrogate:
    names = list(SPECIES_NAMES)

    def __init__(self, model):
        self.model = model.eval()
        self.last_temperature = None
        self.last_pressure = None

    @classmethod
    def from_checkpoint(cls, path):
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        if checkpoint.get("feature_transform", FEATURE_TRANSFORM) != FEATURE_TRANSFORM:
            raise ValueError("Unsupported feature transform")
        model = UVSurrogateNet(checkpoint.get("input_size", 10), checkpoint["hidden_size"], 6)
        model.load_state_dict(checkpoint["model_state_dict"])
        return cls(model)

    @torch.no_grad()
    def solve_batch(self, temperature, pressure, masses):
        features = torch.from_numpy(encode_inputs(temperature, pressure, masses))
        return _decode(self.model(features).cpu().numpy(), masses)

    def solve(self, temperature, pressure, masses):
        t, p, result = self.solve_batch([temperature], [pressure], [masses])
        self.last_temperature, self.last_pressure = float(t[0]), float(p[0])
        return result[0].tolist()

    def get_next_state(self, temperature, pressure, masses):
        return self.solve(temperature, pressure, masses)


@torch.no_grad()
def metrics(model, dataset, indices):
    prediction = model(dataset.x[indices]).numpy()
    target = dataset.y[indices].numpy()
    result = {"weighted_mse": evaluate_loss(model, dataset, indices), "r2": {}}
    for column, name in enumerate(TARGET_NAMES):
        denominator = np.sum((target[:, column] - target[:, column].mean()) ** 2)
        result["r2"][name] = (
            float(1.0 - np.sum((prediction[:, column] - target[:, column]) ** 2 / denominator)
                  ) if denominator > 0.0 else None
        )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--hidden-size", type=int, default=DEFAULT_HIDDEN_SIZE)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--learning-rate", type=float, default=DEFAULT_LEARNING_RATE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)

    dataset = load_dataset(args.dataset)
    model, history = train_model(
        dataset, args.hidden_size, args.epochs, args.batch_size,
        args.learning_rate, args.seed,
    )
    report = {
        name: metrics(model, dataset, indices)
        for name, indices in (
            ("train", dataset.train_indices),
            ("val", dataset.val_indices),
            ("test", dataset.test_indices),
        )
    }
    checkpoint = {
        "model_state_dict": model.state_dict(), "hidden_size": args.hidden_size,
        "input_size": dataset.x.shape[1], "feature_transform": FEATURE_TRANSFORM,
        "species_names": list(SPECIES_NAMES), "target_names": list(TARGET_NAMES),
        "history": history, "metrics": report,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = args.out_dir / f"gas_aq_uv_surrogate_h{args.hidden_size}_e{args.epochs}.pt"
    torch.save(checkpoint, path)
    path.with_suffix(".metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
