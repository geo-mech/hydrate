# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=linspace(-1, 1, jx + 1), y=[-0.5, 0.5], z=linspace(-2, 2, jz + 1)
    )
    model = seepage.create(
        mesh=mesh, dv_relative=0.5,
        fludefs=[Seepage.FluDef(name='h2o')],
        porosity=0.2,
        p=2e6, s=1.0,
        perm=10e-15,
        gravity=[0, 0, -10]
    )
    for cell in model.cells:  # 在z=-1.5的区域设置低密度；在z=1.5的区域设置高密度
        x, _, z = cell.pos
        flu = cell.get_fluid(0)
        if point_distance((x, z), (0, -1.5)) < 0.3:
            flu.mass *= 0.5
            flu.den *= 0.5
        if point_distance((x, z), (0, 1.5)) < 0.3:
            flu.mass *= 1.5
            flu.den *= 1.5
    seepage.set_fa(model, 0, 'z0', seepage.get_z(model))
    model.add_tag('disable_update_den', 'disable_update_vis', 'disable_ther')
    return model


def show(model, jx, jz, caption=None):
    def on_figure(figure):
        figure.suptitle(f'Model when time = {seepage.get_time(model, as_str=True)}')
        angles = linspace(0, np.pi * 2, 100)
        c1 = item('xy', np.cos(angles) * 0.3, np.sin(angles) * 0.3 + 1.5, 'k--')
        c2 = item('xy', np.cos(angles) * 0.3, np.sin(angles) * 0.3 - 1.5, 'r--')
        shape = [jx, jz]
        xy = [seepage.get_x(model, shape=shape), seepage.get_z(model, shape=shape)]
        f1 = item('contourf', *xy, seepage.get_den(model, 0, shape=shape), cbar=dict(label='密度'))
        f2 = item('contourf', *xy, seepage.get_fa(model, 0, 'z0', shape=shape), cbar=dict(label='流体z0'))
        opts = dict(ncols=2, nrows=1, xlabel='x / m', ylabel='z / m', aspect='equal')
        add_axes2(figure, add_items, f1, c1, c2, title='密度', index=1, **opts)
        add_axes2(figure, add_items, f2, c1, c2, title='流体Z0', index=2, **opts)

    plot(on_figure, caption=caption, clear=True)


def main():
    jx, jz = 50, 100
    model = create(jx, jz)
    show(model, jx, jz, caption='初始状态')
    seepage.solve(model, time_max=3600 * 24 * 500, extra_plot=lambda: show(model, jx, jz, caption='最新状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
