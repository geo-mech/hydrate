# ** desc = '两相流，水驱替气体'

from zmlx import *
from zmlx.plt.on_figure import add_axes2
from zmlx.plt.tricontourf import add_tricontourf


def create():
    mesh = create_cube(
        np.linspace(0, 25, 26),
        np.linspace(0, 50, 51), (-0.5, 0.5))

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(y - y1) < 0.1:
            cell.vol = 1.0e8

    model = seepage.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=1e6,
        temperature=280,
        s=(1, 0),
        perm=1e-14,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=[
            Seepage.FluDef(den=50, vis=1.0e-5, name='flu0'),
            Seepage.FluDef(den=1000, vis=1.0e-3,
                           name='flu1')]
    )

    cell = model.get_nearest_cell((x0, y0, 0))
    model.add_injector(
        fluid_id=1,
        flu=cell.get_fluid(1),
        pos=cell.pos,
        radi=0.1,
        opers=[(0, 1.0e-5)])

    seepage.set_dt_max(model, 3600 * 24 * 7)

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'time_max': 100 * 24 * 3600}
    )

    return model


def show(model):
    def on_figure(fig):
        x = as_numpy(model).cells.x
        y = as_numpy(model).cells.y
        p = as_numpy(model).cells.pre
        v0 = as_numpy(model).fluids(0).vol
        v1 = as_numpy(model).fluids(1).vol
        v = v0 + v1
        s0 = v0 / v
        s1 = v1 / v
        args = [fig, add_tricontourf, x, y]
        kwds = dict(aspect='equal', xlabel='x/m', ylabel='y/m', nrows=1, ncols=3)
        add_axes2(*args, p, cbar=dict(label='p'), title='压力', index=1, **kwds)
        add_axes2(*args, s0, cbar=dict(label='s0'), title='flu0 saturation', index=2, **kwds)
        add_axes2(*args, s1, cbar=dict(label='s1'), title='flu1 saturation', index=3, **kwds)
        fig.suptitle(f'时间: {seepage.get_time(model, as_str=True)}')
        fig.tight_layout()

    plot(on_figure)


def main():
    model = create()
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model))


if __name__ == '__main__':
    main()
