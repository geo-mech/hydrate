# ** desc = '侵入逾渗(IP)模型计算油气运移成藏'


from zmlx import *


def create(jx=100, jy=300):
    import random
    mesh = create_cube(
        x=np.linspace(0, 100, jx + 1),
        y=np.linspace(0, 300, jy + 1),
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
    model.set_outlet(
        0, model.get_nearest_node(pos=(50, 300, 0)).index)

    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(30, 0, 0)).index
    inj.phase = 1
    inj.qinj = 1

    inj = model.add_inj()
    inj.node_id = model.get_nearest_node(pos=(70, 0, 0)).index
    inj.phase = 1
    inj.qinj = 0.5

    return model


def solve(model, jx, jy):
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
            ip.show_xy(model, jx=jx, jy=jy)


def execute(gui_mode=True, close_after_done=False):
    jx, jy = 100, 300
    model = create(jx, jy)
    ip.set_x(model, ip.get_x(model) + ip.get_y(model) * 0.3)
    gui.execute(lambda: solve(model, jx, jy), close_after_done=close_after_done,
                disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
