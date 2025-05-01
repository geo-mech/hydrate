# ** desc = '测试：纵向二维。浮力作用下气体运移、水合物成藏过程模拟'

from zmlx import *


def create():
    mesh = create_cube(x=np.linspace(0, 300, 150),
                       y=(-0.5, 0.5),
                       z=np.linspace(0, 500, 250))

    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def get_s(x, y, z):
        if get_distance((x, z), (150, 100)) < 50:
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
        if abs(x - 150) < 20:
            return 1.0e-13
        else:
            return 1.0e-15

    kw = hydrate.create_kwargs(has_inh=True,  # 存在抑制剂
                               has_ch4_in_liq=True,  # 存在溶解气
                               gravity=[0, 0, -10],
                               mesh=mesh, porosity=0.1, pore_modulus=100e6,
                               denc=get_denc, dist=0.1,
                               temperature=get_t, p=get_p, s=get_s,
                               perm=get_k, heat_cond=2.0
                               )
    model = seepage.create(**kw)

    # 用于求解的选项
    model.set_text(key='solve',
                   text=dict(
                       show_cells=dict(
                           dim0=0,
                           dim1=2
                       ),
                       step_max=10000
                   ))
    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
