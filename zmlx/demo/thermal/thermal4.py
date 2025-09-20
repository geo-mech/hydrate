# ** desc = '基于Seepage类的温度场计算'

from zmlx import *


def create(jx, jy):
    model = seepage.create(
        mesh=create_cube(
            np.linspace(-50, 50, jx + 1),
            np.linspace(-50, 50, jy + 1),
            (-0.5, 0.5)),
        temperature=400.0,
        denc=1.0e6,
        heat_cond=1.0,
        dt_max=1.0e6,
        texts={'solve': {'time_max': 3600 * 24 * 365 * 20, }}
    )
    ca_t = model.get_cell_key('temperature')
    ca_mc = model.get_cell_key('mc')
    for x, y in [(-20, 0), (20, 0), (0, -20), (0, 20)]:
        cell = model.get_nearest_cell(pos=[x, y, 0])
        assert isinstance(cell, Seepage.Cell)
        cell.set_attr(ca_t, 300)
        cell.set_attr(ca_mc, 1e10)
    return model


def show(model: Seepage, jx, jy):
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
         caption='温度场')


def main():
    jx, jy = 50, 50
    model = create(jx, jy)
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jy))


if __name__ == '__main__':
    main()
