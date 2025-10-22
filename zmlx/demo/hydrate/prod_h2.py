# ** desc = '水平方向二维的水合物开发过程'


from zmlx import *


def create(jx, jy, xr=None, yr=None):
    if xr is None:
        xr = (-50, 50)
    if yr is None:
        yr = (-50, 50)
    mesh = create_cube(x=np.linspace(*xr, jx + 1), y=np.linspace(*yr, jy + 1), z=(-1, 1))

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 0, 5], vol=1.0e6,
                  area=5, length=1)

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    def boundary(x, y, z):
        return abs(x - x_min) < 1e-3 or abs(x - x_max) < 1e-3 or abs(
            y - y_min) < 1e-3 or abs(y - y_max) < 1e-3

    def is_prod(x, y, z):
        return z > 1

    def get_s(*args):
        if is_prod(*args):
            return {'h2o': 1}
        else:
            return {'h2o': 1, 'ch4_hydrate': 0.4}

    def heat_cond(x, y, z):
        return 1.0 if abs(z) < 1 else 0.0

    kw = hydrate.create_kwargs(
        gravity=[0, 0, 0],
        mesh=mesh,
        porosity=lambda *args: 1e6 if boundary(*args) or is_prod(*args) else 0.3,
        pore_modulus=100e6,
        denc=lambda *args: 1e20 if boundary(*args) else 5e6,
        temperature=285.0,
        p=lambda *args: 3e6 if is_prod(*args) else 10e6,
        s=get_s,
        perm=1e-14,
        heat_cond=heat_cond,
        dt_min=1,
        dt_max=24 * 3600 * 10,
        dv_relative=0.1)

    return seepage.create(**kw)


def show(model: Seepage, jx, jy, caption=None):
    def on_figure(fig):
        opts = dict(ncols=2, nrows=2, xlabel='x', ylabel='y', aspect='equal')
        mask = seepage.get_cell_mask(model=model, zr=[-1, 1])
        x = seepage.get_x(model, shape=[jx, jy], mask=mask)
        y = seepage.get_y(model, shape=[jx, jy], mask=mask)
        args = ['contourf', x, y, ]
        t = seepage.get_t(model, shape=[jx, jy], mask=mask)
        add_axes2(fig, add_items,
                  item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'),
                  title='温度', index=1, **opts)
        p = seepage.get_p(model, shape=[jx, jy], mask=mask)
        add_axes2(fig, add_items,
                  item(*args, p, cbar=dict(label='压力', shrink=0.6), cmap='coolwarm'),
                  title='压力', index=2, **opts)
        v = seepage.get_v(model, shape=[jx, jy], mask=mask)
        index = 3
        for fid in ['ch4', 'ch4_hydrate']:
            s = seepage.get_v(model, fid=fid, shape=[jx, jy], mask=mask) / v
            add_axes2(fig, add_items,
                      item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6), levels=30),
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    plot(on_figure, caption=caption, clear=True,
         suptitle=f'time = {seepage.get_time_str(model)}'
         )


def main():
    jx, jy = 70, 50
    model = create(jx, jy, xr=[-70, 70], yr=[-50, 50])
    gui.hide_console()
    show(model, jx, jy, caption='初始状态')
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy, caption='当前状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
