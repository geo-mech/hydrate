# ** desc = '纵向二维。浮力作用下气体运移、水合物成藏过程模拟（在模型的顶部设置盖层）'

from zmlx import *


def create(jx=150, jz=250):
    mesh = create_cube(
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(0, 500, jz + 1))

    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 11e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        return get_distance((x, z), (150, 10)) < 50

    def get_s(*pos):
        return {'ch4': 1} if is_gas_region(*pos) else {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_porosity(*pos):
        return 0.5 if is_gas_region(*pos) else 0.1

    def get_k(x, y, z):
        if z < np.cos((x - 150) * np.pi * 0.5 / 150) * 80 + 350:
            return 1.0e-15
        else:
            return 0.0

    opts = hydrate.create_opts(
        has_inh=True,  # 存在抑制剂
        has_ch4_in_liq=True,  # 存在溶解气
        gravity=[0, 0, -10],
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,
        denc=get_denc,
        dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0, dt_max=3600 * 24 * 30
    )
    model = seepage.create(**opts)
    return model


def show(model: Seepage, jx, jz, caption=None):
    def on_figure(fig):
        opts = dict(ncols=3, nrows=1, xlabel='x', ylabel='z', aspect='equal')
        angles = np.linspace(0, np.pi, 100)
        c1 = item('xy', np.cos(angles) * 50 + 150, np.sin(angles) * 50 + 10, 'r--')
        vx = np.linspace(10, 290, 100)
        vy = np.cos((vx - 150) * np.pi * 0.5 / 150) * 80 + 350
        c2 = item('xy', vx, vy, 'k--')
        x = seepage.get_x(model, shape=[jx, jz])
        z = seepage.get_z(model, shape=[jx, jz])
        args = ['contourf', x, z, ]
        t = seepage.get_t(model, shape=[jx, jz])
        add_axes2(fig, add_items,
                  item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'), c1, c2,
                  title='温度', index=1, **opts)
        v = seepage.get_v(model, shape=[jx, jz])
        index = 2
        for fid in ['ch4', 'ch4_hydrate']:
            s = seepage.get_v(model, fid=fid, shape=[jx, jz]) / v
            add_axes2(fig, add_items,
                      item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6), levels=30), c1, c2,
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    plot(on_figure, caption=caption, clear=True, tight_layout=True,
         suptitle=f'time = {seepage.get_time_str(model)}'
         )


def main():
    gui.hide_console()
    jx, jz = 50, 100
    model = create(jx, jz)
    show(model, jx, jz, caption='初始状态')
    seepage.solve(model=model, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
                  time_max=100 * 365 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
