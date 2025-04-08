# ** desc = '侵入逾渗(IP)模型计算油气运移成藏(测试更多的批量接口)'


import random

import numpy as np

from zml import InvasionPercolation, get_pointer64
from zmlx.plt.plot_on_axes import plot_on_axes
from zmlx.seepage_mesh.cube import create_cube
from zmlx.ui import gui


def create():
    mesh = create_cube(
        x=np.linspace(0, 100, 100),
        y=np.linspace(0, 300, 300),
        z=(0, 1))
    model = InvasionPercolation()
    random.seed(1000000)
    for cell in mesh.cells:
        node = model.add_node()
        node.pos = cell.pos
        node.phase = 0
        node.radi = random.uniform(1.0, 2.0)
    node_n = model.node_n
    print(f'Load nodes. Count = {node_n}')

    for face in mesh.faces:
        i0 = face.get_cell(0).index
        i1 = face.get_cell(1).index
        assert node_n > i0 != i1 < node_n
        bond = model.add_bond(i0, i1)
        bond.radi = random.uniform(0.5, 1.0)
    bond_n = model.bond_n
    print(f'Load bonds. Count = {bond_n}')

    model.gravity = (0, -0.001, 0)
    model.set_density(0, 1.0)
    model.set_density(1, 0.1)

    model.outlet_n = 1
    model.read_outlet(get_pointer64(np.asarray(
        [model.get_nearest_node(pos=(50, 300, 0)).index], dtype=np.float64))
    )

    i0 = model.get_nearest_node(pos=(30, 0, 0)).index
    i1 = model.get_nearest_node(pos=(70, 0, 0)).index

    model.inj_n = 2
    model.read_inj_node_id(
        get_pointer64(np.asarray([i0, i1], dtype=np.float64))
    )
    model.read_inj_phase(
        get_pointer64(np.asarray([1, 1], dtype=np.float64))
    )
    model.read_inj_q(
        get_pointer64(np.asarray([1, 0.5], dtype=np.float64))
    )
    return model


def show(model):
    def on_axes(ax):
        x = model.nodes_write(-1)
        y = model.nodes_write(-2)
        v = model.nodes_write(-4)
        mask = v < 0.5
        ax.scatter(x[mask], y[mask], c='tab:blue', s=3, label='Water',
                   alpha=0.2, edgecolors='none')
        mask = [not m for m in mask]
        ax.scatter(x[mask], y[mask], c='tab:orange', s=8, label='Oil',
                   alpha=0.7, edgecolors='none')

    plot_on_axes(on_axes, show_legend=True, grid=True, axis='equal',
                 caption='侵入过程', gui_only=True)


def solve(model):
    for step in range(4000):
        gui.break_point()
        model.iterate()
        if step % 50 == 0:
            print(f'step = {step}, time = {model.time}, ', end='')
            print('Invade operations: ', end='')
            for idx in range(model.oper_n):
                oper = model.get_oper(idx)
                print(f'({oper.get_node(0).index} -> {oper.get_node(1).index})',
                      end=', ')
            print('')
            show(model)


def execute(gui_mode=True, close_after_done=False):
    model = create()

    # 读取node的位置
    x = np.zeros(shape=model.node_n)
    y = np.zeros(shape=model.node_n)
    model.write_pos(0, get_pointer64(x))
    model.write_pos(1, get_pointer64(y))

    # 修改x
    x = x + y * 0.3
    model.read_pos(0, get_pointer64(x))

    # 求解
    gui.execute(lambda: solve(model), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
