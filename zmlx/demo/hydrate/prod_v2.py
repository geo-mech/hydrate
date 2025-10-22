# ** desc = '竖直方向二维的水合物开发过程'

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建模型
    """
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1, upper=30,
                     lower=30)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, -50], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        if z > -30 or z < -70:
            return 1.0e-15
        else:
            return 1.0e-14

    def get_p(x, y, z):
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        return 285 - z * 0.04

    def denc(*pos):
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        if is_upper(x, y, z):  # 顶部固定压力
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词
    kw = hydrate.create_kwargs(
        gravity=[0, 0, -10],
        dt_min=1,
        dt_max=24 * 3600,
        dv_relative=0.1,
        mesh=mesh,
        porosity=get_fai,
        pore_modulus=100e6,
        denc=denc,
        temperature=get_t,
        p=get_p,
        s=get_s,
        perm=get_k,
        heat_cond=heat_cond,
        prods=[{'index': mesh.cell_number - 1,
                't': [0, 1e20], 'p': [3e6, 3e6]}]
    )
    model = seepage.create(**kw)

    # 用于solve的选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},
              'time_max': 3 * 365 * 24 * 3600,
              }
    )
    # 返回模型
    return model


def show(model: Seepage, caption=None):
    def on_figure(fig):
        opts = dict(ncols=4, nrows=1, xlabel='x', ylabel='z', aspect='equal')
        mask = seepage.get_cell_mask(model=model, yr=[-1, 1])
        x = seepage.get_x(model, mask=mask)
        z = seepage.get_z(model, mask=mask)
        args = ['tricontourf', x, z, ]
        t = seepage.get_t(model, mask=mask)
        add_axes2(
            fig, add_items,
            item(*args, t, cbar=dict(shrink=0.6), cmap='coolwarm'),
            title='温度', index=1, **opts)
        p = seepage.get_p(model, mask=mask)
        ax = add_axes2(
            fig, add_items,
            item(*args, p, cbar=dict(shrink=0.6), cmap='coolwarm'),
            title='压力', index=2, **opts)
        ax.set_yticks([])

        v = seepage.get_v(model, mask=mask)
        index = 3
        for fid in ['ch4', 'ch4_hydrate']:
            s = seepage.get_v(model, fid=fid, mask=mask) / v
            ax = add_axes2(
                fig, add_items,
                item(*args, s, cbar=dict(shrink=0.6)),
                title=f'{fid}饱和度', index=index, **opts)
            ax.set_yticks([])
            index += 1

    plot(on_figure, caption=caption, clear=True,
         suptitle=f'time = {seepage.get_time_str(model)}'
         )


def main():
    model = create()
    gui.hide_console()
    show(model, caption='初始状态')
    seepage.solve(model, extra_plot=lambda: show(model, caption='当前状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
