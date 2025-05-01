# ** desc = '测试：纵向二维。浮力作用下气体运移成藏过程模拟'

from zmlx import *


def create():
    mesh = create_cube(
        x=linspace(0, 300, 150),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, 250)
    )

    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def get_s(x, y, z):
        if get_distance((x, y, z), (150, 0, -400)) < 50:
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

    model = seepage.create(
        mesh, porosity=0.1, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24, gravity=(0, 0, -10))

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'show_cells': {'dim0': 0, 'dim1': 2},
              'step_max': 10000,
              }
    )

    return model


if __name__ == '__main__':
    seepage.solve(create(), close_after_done=False)
