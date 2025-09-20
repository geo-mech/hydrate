# ** desc = '重力驱动下的气水分层'


from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(-500, 0, jz + 1)
    )

    def get_s(x, y, z):
        if x > 150:
            return {'ch4': 0.2, 'h2o': 0.8}
        else:
            return {'ch4': 0.8, 'h2o': 0.2}

    model = seepage.create(
        mesh, porosity=0.1, pore_modulus=100e6,
        denc=1.0e6,
        temperature=280,
        p=10e6,
        s=get_s,
        perm=1.0e-15,
        heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24 * 365,
        gravity=(0, 0, -10))

    return model


def show(model, jx, jz, caption=None):
    def on_figure(fig):
        args = [fig, add_contourf, seepage.get_x(model, shape=(jx, jz)), seepage.get_z(model, shape=(jx, jz))]
        p = seepage.get_p(model, shape=(jx, jz))
        v = seepage.get_v(model, shape=(jx, jz))
        s0 = seepage.get_v(model, fid=0, shape=(jx, jz)) / v
        s1 = seepage.get_v(model, fid=1, shape=(jx, jz)) / v
        opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=3)
        add_axes2(*args, p, cbar=dict(label='pressure', shrink=0.7), title='pressure', index=1, cmap='coolwarm', **opts)
        add_axes2(*args, s0, cbar=dict(label='ch4 saturation', shrink=0.7), title='ch4 saturation', index=2, **opts)
        add_axes2(*args, s1, cbar=dict(label='h2o saturation', shrink=0.7), title='h2o saturation', index=3, **opts)
        fig.suptitle(f'时间: {seepage.get_time(model, as_str=True)}')
        fig.tight_layout()

    plot(on_figure, caption=caption)


def main():
    jx, jz = 30, 100
    model = create(jx, jz)
    gui.hide_console()
    show(model, jx, jz, caption='初始状态')
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
                  time_forward=3600 * 24 * 365 * 100
                  )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
