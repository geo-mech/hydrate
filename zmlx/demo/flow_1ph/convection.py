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


def fig_data(model, jx, jz):
    angles = linspace(0, np.pi * 2, 100)
    c1 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 + 1.5, 'k--')
    c2 = fig.curve(np.cos(angles) * 0.3, np.sin(angles) * 0.3 - 1.5, 'r--')
    shape = [jx, jz]
    xy = [seepage.get_x(model, shape=shape), seepage.get_z(model, shape=shape)]
    f1 = fig.contourf(*xy, seepage.get_den(model, 0, shape=shape), cbar=dict(label='密度'))
    f2 = fig.contourf(*xy, seepage.get_fa(model, 0, 'z0', shape=shape), cbar=dict(label='流体z0'))
    opts = dict(xlabel='x / m', ylabel='z / m', aspect='equal')
    return fig.auto_layout(
        fig.axes2(
            f1, c1, c2, title='密度', **opts
        ),
        fig.axes2(
            f2, c1, c2, title='流体Z0', **opts
        ),
        fig.suptitle(f'Model when time = {seepage.get_time(model, as_str=True)}'),
        aspect_ratio=0.5,
    )


def main():
    jx, jz = 50, 100
    model = create(jx, jz)
    fig.show(fig_data(model, jx, jz), caption='初始状态', clear=True)
    seepage.solve(model, time_max=3600 * 24 * 500,
                  extra_plot=lambda: fig.show(fig_data(model, jx, jz), caption='最新状态', clear=True)
                  )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
