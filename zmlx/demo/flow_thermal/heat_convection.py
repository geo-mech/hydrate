# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=linspace(-0.6, 0.6, jx + 1), y=[-0.5, 0.5], z=linspace(-1, 1, jz + 1)
    )

    def is_region1(x, y, z):
        return point_distance([x, z], [-0.1, 0.5]) < 0.2

    def is_region2(x, y, z):
        return point_distance([x, z], [0.1, -0.5]) < 0.2

    def get_denc(x, y, z):
        return 1.0e20 if is_region1(x, y, z) or is_region2(x, y, z) else 1.0e6

    def get_temp(x, y, z):
        if is_region1(x, y, z):
            return 280
        if is_region2(x, y, z):
            return 320
        else:
            return 300

    def dist(x, y, z):
        return 1.0

    model = seepage.create(
        mesh=mesh, dv_relative=0.5,
        fludefs=[h2o.create(t_min=272.0, t_max=340.0, p_min=1e6, p_max=40e6,
                            name='h2o')],
        porosity=0.2,
        p=5e6, s=1.0,
        perm=1e-12,
        temperature=get_temp, denc=get_denc,
        gravity=[0, 0, -10],
        dist=dist,
    )

    model.add_tag('disable_ther')
    seepage.set_fa(model, 0, 'z0', seepage.get_z(model))

    return model


def show(model, jx, jz, caption=None):
    def on_figure(figure):
        opts = dict(ncols=3, nrows=1, xlabel='x', ylabel='z', aspect='equal')
        x = seepage.get_x(model, shape=[jx, jz])
        z = seepage.get_z(model, shape=[jx, jz])
        args = ['contourf', x, z, ]

        angles = linspace(0, np.pi * 2, 100)
        c1 = item('xy', 0.2 * np.cos(angles) + 0.1, 0.2 * np.sin(angles) - 0.5, 'r--')
        c2 = item('xy', 0.2 * np.cos(angles) - 0.1, 0.2 * np.sin(angles) + 0.5, 'k--')

        temp = item(*args, seepage.get_fa(model, 0, 'temperature', shape=[jx, jz]),
                    cbar=dict(label='温度', shrink=0.6))
        den = item(*args, seepage.get_den(model, 0, shape=[jx, jz]),
                   cbar=dict(label='密度', shrink=0.6))
        z0 = item(*args, seepage.get_fa(model, 0, 'z0', shape=[jx, jz]),
                  cbar=dict(label='z0', shrink=0.6))

        add_axes2(figure, add_items, temp, c1, c2, title='流体温度', index=1, **opts)
        add_axes2(figure, add_items, den, c1, c2, title='密度', index=2, **opts)
        add_axes2(figure, add_items, z0, c1, c2, title='流体z0', index=3, **opts)

    plot(on_figure, caption=caption, clear=True, tight_layout=True,
         suptitle=f'time = {seepage.get_time(model, as_str=True)}'
         )


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    show(model, jx, jz, caption='初始状态')
    seepage.solve(model, time_max=3600 * 24 * 500, extra_plot=lambda: show(model, jx, jz, caption='实时状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
