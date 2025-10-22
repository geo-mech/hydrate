# ** desc = '侵入逾渗(IP)模型计算油气运移成藏(测试更多的批量接口，包括创建过程)'


from zmlx import *


def create(jx=100, jy=300):
    import random
    mesh = create_cube(
        x=np.linspace(0, 100, jx + 1),
        y=np.linspace(0, 300, jy + 1),
        z=(0, 1))

    node_pos = np.asarray([c.pos for c in mesh.cells])
    lnks = np.asarray([f.link for f in mesh.faces])

    model = InvasionPercolation()
    random.seed(1000000)
    ip.set_nodes(
        model, mesh.cell_number,
        x=node_pos[:, 0], y=node_pos[:, 1], z=node_pos[:, 2],
        phase=0,
        radi=[random.uniform(1.0, 2.0) for _ in range(mesh.cell_number)])
    node_n = model.node_n
    print(f'Load nodes. Count = {node_n}')

    ip.set_bonds(
        model, mesh.face_number, node0=lnks[:, 0], node1=lnks[:, 1],
        radi=[random.uniform(0.5, 1.0) for _ in range(mesh.face_number)])
    bond_n = model.bond_n
    print(f'Load bonds. Count = {bond_n}')

    model.gravity = (0, -0.001, 0)
    model.set_density(0, 1.0)
    model.set_density(1, 0.1)

    model.outlet_n = 1
    model.read_outlet(
        get_pointer64([model.get_nearest_node(pos=(50, 300, 0)).index],
                      readonly=True))

    i0 = model.get_nearest_node(pos=(30, 0, 0)).index
    i1 = model.get_nearest_node(pos=(70, 0, 0)).index

    model.inj_n = 2
    model.read_inj_node_id(
        get_pointer64([i0, i1], readonly=True))
    model.read_inj_phase(
        get_pointer64([1, 1], readonly=True))
    model.read_inj_q(
        get_pointer64([1, 0.5], readonly=True))
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
