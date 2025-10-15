# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


def create(jx, jy):
    """
    创建模型(不设置任何边界条件)
    """
    model = seepage.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),
            np.linspace(-50, 50, jy + 1),
            (-0.5, 0.5)),
        temperature=400.0,
        denc=1.0e6,
        heat_cond=1.0,
        dt_max=3600*24*7,
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


def set_well(model, temp):
    """
    设置井的温度
    """
    ca_t = model.get_cell_key('temperature')
    ca_mc = model.get_cell_key('mc')
    for x, y in [(-20, 0), (20, 0), (0, -20), (0, 20)]:
        cell = model.get_nearest_cell(pos=[x, y, 0])
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, temp)
        cell.set_attr(ca_mc, 1e10)


def show(model: Seepage, jx, jy, caption=None):
    x = seepage.get_x(model, shape=(jx, jy))
    y = seepage.get_y(model, shape=(jy, jx))
    t = seepage.get_ca(model, model.get_cell_key('temperature'), shape=(jx, jy)) - 300
    cmap = 'coolwarm'
    items = [item('surf', x, y, t * 100, t, cbar={'label': 'temperature (K)', 'shrink': 0.7}, cmap=cmap),
             item('contourf', x, y, t, cmap=cmap)
             ]
    plot(add_axes3, add_items, *items,
         xlabel="x/m", ylabel="y/m", title=f'Time = {seepage.get_time(model, as_str=True)}',
         tight_layout=True,
         caption=caption)


def main():
    jx, jy = 50, 50
    model = create(jx, jy)
    backup_mc(model)  # 备份mc属性

    set_well(model, 500)
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段1'), time_forward=3600 * 24 * 365 * 5)

    restore_mc(model)  # 恢复mc属性
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段2'), time_forward=3600 * 24 * 365 * 2)

    set_well(model, 300)
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='阶段3'), time_forward=3600 * 24 * 365 * 5)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
