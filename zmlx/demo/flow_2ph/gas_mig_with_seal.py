# ** desc = '浮力作用下气体运移成藏过程模拟(加入隔挡层)'

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    def get_region_id(x, y, z):
        """
        定义在不同的区域所使用的毛管压力曲线的ID (从0开始编号)
        """
        return 1 if 0 <= x <= 200 and -250 <= z <= -200 else 0

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

    capillary.add_setting(
        model, fid0='ch4', fid1='h2o', get_idx=get_region_id,
        data=[[[0, 1], [0, 1]],
              [[0, 1], [0, 5e6]]
              ]
    )

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, }
    )

    return model


def show(model, jx, jz):
    def on_figure(fig):
        x = seepage.get_x(model, shape=(jx, jz))
        z = seepage.get_z(model, shape=(jx, jz))
        p = seepage.get_p(model, shape=(jx, jz))
        v0 = seepage.get_v(model, fid=0, shape=(jx, jz))
        v1 = seepage.get_v(model, fid=1, shape=(jx, jz))
        v = v0 + v1
        args = [fig, add_contourf, x, z]
        opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=3)

        def add_rect(ax):
            ax.plot([0, 200, 200, 0], [-250, -250, -200, -200], color='r', linewidth=1)
            angles = np.linspace(0, np.pi, 100)
            ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

        ax = add_axes2(*args, p, cbar=dict(label='pressure', shrink=0.6), title='pressure', cmap='coolwarm', index=1,
                       **opts)
        add_rect(ax)
        ax = add_axes2(*args, v0 / v, cbar=dict(label='ch4 saturation', shrink=0.6), title='ch4 saturation', index=2,
                       **opts)
        add_rect(ax)
        ax = add_axes2(*args, v1 / v, cbar=dict(label='h2o saturation', shrink=0.6), title='h2o saturation', index=3,
                       **opts)
        add_rect(ax)

    plot(on_figure, caption=f'Seepage({model.handle})', suptitle=f'时间: {seepage.get_time(model, as_str=True)}', tight_layout=True)


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    seepage.solve(model, extra_plot=lambda: show(model, jx, jz))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
