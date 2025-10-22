# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


def create(jx, jy):
    """
    创建模型(不设置任何边界条件)
    """
    f = load_igg(xmin=-50, xmax=50, ymin=-50, ymax=50)

    def heat_cond(x, y, z):
        if f(x, y) > 0.5:
            return 1
        else:
            return 0.0001

    model = seepage.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),
            np.linspace(-50, 50, jy + 1),
            (-0.5, 0.5)),
        temperature=400.0,
        denc=1.0e6,
        heat_cond=heat_cond,
        dt_max=3600 * 24 * 7,
    )
    return model


def backup_mc(model: Seepage):
    ca_mc = model.get_cell_key('mc')
    ca_backup = model.reg_cell_key('backup')
    cells = as_numpy(model).cells
    cells.set(ca_backup, cells.get(ca_mc))


def restore_mc(model: Seepage):
    ca_mc = model.get_cell_key('mc')
    ca_backup = model.get_cell_key('backup')
    cells = as_numpy(model).cells
    cells.set(ca_mc, cells.get(ca_backup))


def set_well(model, temp, poses):
    """
    设置井的温度
    """
    ca_t = model.get_cell_key('temperature')
    ca_mc = model.get_cell_key('mc')
    for x, y in poses:
        cell = model.get_nearest_cell(pos=[x, y, 0])
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, temp)
        cell.set_attr(ca_mc, 1e10)


def show(model: Seepage, jx, jy, caption=None):
    x = seepage.get_x(model, shape=(jx, jy))
    y = seepage.get_y(model, shape=(jy, jx))
    t = seepage.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300
    items = [item('contourf', x, y, t, cmap='coolwarm', cbar={'label': 'temperature (K)', 'shrink': 0.7})]
    plot(add_axes2, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {seepage.get_time(model, as_str=True)}',
         tight_layout=True,
         caption=caption, aspect='equal')


def main():
    jx, jy = 100, 100
    model = create(jx, jy)
    backup_mc(model)  # 备份mc属性

    set_well(model, 500, poses=[(0, -45), (0, 45)])
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段1'), time_forward=3600 * 24 * 365 * 100)

    restore_mc(model)  # 恢复mc属性
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段2'), time_forward=3600 * 24 * 365 * 20)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
