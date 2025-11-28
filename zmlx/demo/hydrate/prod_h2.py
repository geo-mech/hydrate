# ** desc = '水平方向二维的水合物开发过程'


from zmlx import *
from zmlx.config.hydrate import show_2d_v2


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
    show_2d_v2(model, shape=(jx, jy), dim0=0, dim1=1, zr=[-1, 1], caption=caption)


def main():
    jx, jy = 70, 50
    model = create(jx, jy, xr=[-70, 70], yr=[-50, 50])
    seepage.solve(model, extra_plot=lambda: show(model, jx, jy))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
