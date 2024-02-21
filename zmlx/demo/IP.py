# ** desc = '侵入逾渗(IP)模型计算油气运移成藏'


import random

import numpy as np

from zml import SeepageMesh, InvasionPercolation
from zmlx.ui import gui


def create():
    mesh = SeepageMesh.create_cube(x=np.linspace(0, 100, 100), y=np.linspace(0, 300, 300), z=(0, 1))
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
    model.set_outlet(0, model.get_nearest_node(pos=(50, 300, 0)).index)

    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(30, 0, 0)).index
    inj.phase = 1
    inj.qinj = 1

    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(70, 0, 0)).index
    inj.phase = 1
    inj.qinj = 0.5

    return model


def show(model):
    if gui.exists():
        def f(fig):
            x = model.nodes_write(-1)
            y = model.nodes_write(-2)
            v = model.nodes_write(-4)
            ax = fig.add_subplot()
            mask = v < 0.5
            ax.scatter(x[mask], y[mask], c='tab:blue', s=3, label='Water',
                       alpha=0.2, edgecolors='none')
            mask = [not m for m in mask]
            ax.scatter(x[mask], y[mask], c='tab:orange', s=8, label='Oil',
                       alpha=0.7, edgecolors='none')
            ax.legend()
            ax.grid(True)
            ax.axis('equal')

        gui.plot(f, clear=True, caption='侵入过程')  # 加上clear，清除掉之前的绘图


def solve(model):
    for step in range(4000):
        gui.break_point()
        model.iterate()
        if step % 50 == 0:
            print(f'step = {step}, time = {model.time}, ', end='')
            print('Invade operations: ', end='')
            for idx in range(model.oper_n):
                oper = model.get_oper(idx)
                print(f'({oper.get_node(0).index} -> {oper.get_node(1).index})', end=', ')
            print('')
            show(model)


def execute(gui_mode=True, close_after_done=False):
    gui.execute(lambda: solve(create()), close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
