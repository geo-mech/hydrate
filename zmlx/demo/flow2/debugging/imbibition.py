# ** desc = '模拟自发的渗吸过程'

from zmlx import *


def create(jx, jy):
    mesh = create_cube(
        x=linspace(-0.5, 0.5, jx + 1),
        y=linspace(-0.5, 0.5, jy + 1),
        z=[-0.5, 0.5]
    )

    def get_s(x, y, z):
        if x < 0:
            return {'ch4': 1}
        else:
            return {'h2o': 1}

    def get_k(x, y, z):
        if abs(x) < 0.2 < abs(y):
            return 0
        else:
            return 1.0e-14

    model = seepage.create(
        mesh, porosity=0.1, pore_modulus=100e6,
        denc=1.0e6, dist=0.1,
        temperature=280, p=1e6, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24 * 30.0, gravity=(0, 0, -10)
    )

    def get_region_id(x, y, z):
        return 1 if x < 0 else 0

    capillary.add(
        model, fid0='ch4', fid1='h2o', get_idx=get_region_id,
        data=[[[0, 1], [0, 1]],
              [[0, 1], [1e6, 5e6]]
              ]
    )
    model.set_kr(saturation=[0, 1], kr=[0, 1])
    seepage.set_dt_max(model, 3600 * 24 * 10)

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 600}
    )

    return model


def show(model, jx, jy, caption=None):
    def on_figure(fig):
        x = seepage.get_x(model, shape=(jx, jy))
        y = seepage.get_y(model, shape=(jx, jy))
        v0 = seepage.get_v(model, fid=0, shape=(jx, jy))
        v1 = seepage.get_v(model, fid=1, shape=(jx, jy))
        vv = v0 + v1
        add_axes2(fig, add_contourf, x, y, v0 / vv, cbar=dict(label='s0', shrink=0.6),
                  title=f'时间: {seepage.get_time(model, as_str=True)}',
                  aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=2, index=1
                  )
        add_axes2(fig, add_contourf, x, y, v1 / vv, cbar=dict(label='s1', shrink=0.6),
                  title=f'时间: {seepage.get_time(model, as_str=True)}',
                  aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=2, index=2
                  )
        fig.tight_layout()

    plot(on_figure, caption=caption)


def main():
    jx, jy = 30, 30
    model = create(jx, jy)
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='当前状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
