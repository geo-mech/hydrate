# ** desc = '浮力作用下气体运移成藏过程模拟'

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

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

    def get_k(x, y, z):
        return 1.0e-14

    def get_porosity(x, y, z):
        if is_gas_region(x, y, z):
            return 1.0  # 使得有更多的气体
        else:
            return 0.1

    model = seepage.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24 * 30.0, gravity=(0, 0, -10)
    )

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, }
    )

    return model


def show(model, jx, jz, caption=None):
    def on_figure(fig):
        x = seepage.get_x(model, shape=(jx, jz))
        z = seepage.get_z(model, shape=(jx, jz))
        p = seepage.get_p(model, shape=(jx, jz))
        v0 = seepage.get_v(model, fid=0, shape=(jx, jz))
        v1 = seepage.get_v(model, fid=1, shape=(jx, jz))
        v = v0 + v1
        args = [fig, add_contourf, x, z]
        opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=3)
        angles = np.linspace(0, np.pi,100)
        ax = add_axes2(*args, p, cbar=dict(label='p', shrink=0.6), title='pressure', cmap='coolwarm', index=1, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'k--')
        ax = add_axes2(*args, v0 / v, cbar=dict(label='s0', shrink=0.6), title='ch4 saturation', index=2, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')
        ax = add_axes2(*args, v1 / v, cbar=dict(label='s1', shrink=0.6), title='h2o saturation', index=3, **opts)
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')
        fig.suptitle(f'时间: {seepage.get_time(model, as_str=True)}')
        fig.tight_layout()

    plot(on_figure, caption=caption)


def main():
    jx = 60
    jz = 100
    model = create(jx, jz)
    seepage.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jz, caption='当前状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
