# ** desc = '侵入逾渗(IP)模型计算油气运移成藏(测试更多的批量接口)'


import random

from zmlx import *


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
            ip.show_xy(model)


def execute(gui_mode=True, close_after_done=False):
    model = create()
    ip.set_x(model, ip.get_x(model) + ip.get_y(model) * 0.3)
    gui.execute(lambda: solve(model), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
