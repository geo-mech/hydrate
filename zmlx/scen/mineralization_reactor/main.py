import argparse
import sys
from pathlib import Path


def ensure_hydrate_root():
    root = str(Path(__file__).resolve().parents[3])
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


ensure_hydrate_root()

from zmlx.tfc import iterate
from zmlx.scen.mineralization_reactor import (
    MINERAL_COMPONENTS,
    Mineralization,
    create,
    key_fields,
    mineralization_reaction,
    scene_state,
    show_xz,
    state_from_cell,
)


def create_state_ini(scene, length, depth):
    base = scene_state(scene)

    def get_state(x, y, z):
        xi = min(max(float(x) / max(float(length), 1.0e-30), 0.0), 1.0)
        zi = min(max(-float(z) / max(float(depth), 1.0e-30), 0.0), 1.0)
        state = dict(base)
        state.pop('H2O', None)
        for mineral in MINERAL_COMPONENTS.values():
            state.pop(mineral, None)
        front = (1.0 - xi) * (0.75 + 0.25 * zi)
        state['CO2(aq)'] = base['CO2(aq)'] * (1.0 + 0.8 * front)
        state['CO2(g)'] = 1.0e-8 * max(front, 0.05)
        state['Ca+2'] = base['Ca+2'] * (0.90 + 0.10 * zi)
        state['Mg+2'] = base['Mg+2'] * (0.90 + 0.10 * zi)
        return state

    return get_state


def build_parser():
    parser = argparse.ArgumentParser(description='Run and show a local mineralization reactor demo.')
    parser.add_argument('--nogui', action='store_true', help='Run without opening the IGG-Hydrate GUI.')
    parser.add_argument('--scene', default='saline_aquifer',
                        choices=['permafrost', 'seabed', 'saline_aquifer', 'basalt'])
    parser.add_argument('--nx', type=int, default=8)
    parser.add_argument('--nz', type=int, default=4)
    parser.add_argument('--length', type=float, default=80.0)
    parser.add_argument('--depth', type=float, default=30.0)
    parser.add_argument('--dt', type=float, default=600.0)
    parser.add_argument('--temperature', type=float, default=298.15)
    parser.add_argument('--t-gradient', type=float, default=0.03)
    parser.add_argument('--pressure', type=float, default=1.0e7)
    parser.add_argument('--p-gradient', type=float, default=1.0e4)
    parser.add_argument('--surface-area', type=float, default=None)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    text = f'scene={args.scene}'
    if args.surface_area is not None:
        text += f';sa={args.surface_area:g}'
    mineralization = Mineralization.from_text(text)
    model = create(
        shape=(args.nx, 1, args.nz),
        size=(args.length, 1.0, args.depth),
        temperature=lambda x, y, z: args.temperature - args.t_gradient * z,
        pressure=lambda x, y, z: args.pressure - args.p_gradient * z,
        mineralization=mineralization,
        state_ini=create_state_ini(args.scene, args.length, args.depth))
    iterate(model, dt=args.dt, slots={'mineralization_reaction': mineralization_reaction})

    cell = model.get_cell(0)
    keys = key_fields(model)
    state = state_from_cell(cell)
    print('Mineralization reactor demo')
    print(f'scene: {args.scene}')
    print(f'cells: {model.cell_number}')
    print(f'pH: {cell.get_attr(keys["pH"]):.6g}')
    print(f'Ca+2 kg: {state["Ca+2"]:.6g}')
    print(f'CO2(aq) kg: {state["CO2(aq)"]:.6g}')
    print(f'Calcite kg: {state["Calcite"]:.6g}')
    print(f'reaktoro_succeeded: {cell.get_attr(keys["reaktoro_succeeded"]):.0f}')
    if not args.nogui:
        show_xz(model, caption=f'Mineralization reactor: {args.scene}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
