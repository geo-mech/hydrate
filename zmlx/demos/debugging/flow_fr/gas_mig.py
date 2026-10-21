"""
在浮力的驱动下，气体向上运移。
"""
from zmlx import *


def create(mesh: SeepageMesh):
    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def get_s(x, y, z):
        if is_gas_region(x, y, z):
            return {'ch4': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_porosity(x, y, z):
        if is_gas_region(x, y, z):
            return 1.0  # 使得有更多的气体
        else:
            return 0.1

    model = tfc.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=1.0e-14, heat_cond=2.0,
        fludefs=[FluDef(name='ch4', vis=1.0e-5, den=10),
                 FluDef(name='h2o', vis=1.0e-3, den=1000)],
        dt_max=3600 * 24 * 30.0,
        gravity=(0, 0, -10)
    )
    assert isinstance(model, Seepage)
    model.add_tag('disable_update_den', 'disable_update_vis')

    return model


def get_fracture_mesh(mesh: SeepageMesh, fractures: list):
    indexes = [None] * mesh.cell_number
    fracture_mesh = SeepageMesh()
    for x0, z0, x1, z1 in fractures:
        print(f'添加裂缝: {x0}, {z0}, {x1}, {z1}')
        dx = (x1 - x0) / 200
        dz = (z1 - z0) / 200
        cell_indexes = []
        for i in range(200):
            x = x0 + dx * i
            z = z0 + dz * i
            cell = mesh.get_nearest_cell(pos=[x, 0, z])
            assert isinstance(cell, SeepageMesh.Cell)
            if indexes[cell.index] is None:
                new_cell = fracture_mesh.add_cell(pos=cell.pos, vol=cell.vol)
                indexes[cell.index] = new_cell.index
                if new_cell.index not in cell_indexes:
                    cell_indexes.append(new_cell.index)

        for i in range(1, len(cell_indexes)):
            i0 = cell_indexes[i - 1]
            i1 = cell_indexes[i]
            fracture_mesh.add_face(i0, i1, dist=1, area=10)

    return indexes, fracture_mesh


def show(model, jx, jz, caption=None):
    def on_figure(fig):
        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        p = tfc.get_p(model, shape=(jx, jz))
        v0 = tfc.get_v(model, fid=0, shape=(jx, jz))
        v1 = tfc.get_v(model, fid=1, shape=(jx, jz))
        v = v0 + v1
        args = [fig, add_contourf, x, z]
        opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=3)
        angles = np.linspace(0, np.pi, 100)
        ax = add_axes2(*args, p, cbar=dict(label='p', shrink=0.6), title='pressure', cmap='coolwarm', index=1, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'k--')
        ax = add_axes2(*args, v0 / v, cbar=dict(label='s0', shrink=0.6), title='ch4 saturation', index=2, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')
        ax = add_axes2(*args, v1 / v, cbar=dict(label='s1', shrink=0.6), title='h2o saturation', index=3, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

    plot(on_figure, caption=caption, suptitle=f'时间: {tfc.get_time(model, as_str=True)}', tight_layout=True)


def solve(model: Seepage, time_max=None, extra_plot=None):
    """
    求解模型，并尝试将结果保存到folder.
    """

    def plot_():
        if extra_plot is not None:
            extra_plot()

    # 执行最终的迭代
    gui_iter = get_gui_iter(tfc.iterate, plot=plot_)

    if time_max is None:  # 给定默认值
        time_max = 1.0e100

    while tfc.get_time(model) < time_max:
        gui.break_point()
        gui_iter(model)

        if tfc.get_step(model) % 20 == 0:
            print(
                f'step={tfc.get_step(model)}, dt={tfc.get_dt_str(model)}, '
                f'time={tfc.get_time_str(model)}')
    plot_()


def main():
    jx, jz = 60, 100

    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    model = create(mesh)
    solve(model, extra_plot=lambda: show(model, jx, jz, caption='当前状态'), time_max=3600 * 24 * 365 * 6)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
