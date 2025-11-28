# ** desc = '纵向二维。浮力作用下气体运移、水合物成藏过程模拟（在模型的中间设置高渗透率的通道）'

from zmlx import *
from zmlx.config.hydrate import show_2d_v2


def create(jx=150, jz=250):
    mesh = create_cube(
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(0, 500, jz + 1))

    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        return get_distance((x, z), (150, 100)) < 50

    def get_s(*pos):
        return {'ch4': 1} if is_gas_region(*pos) else {'h2o': 1}

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

    def get_porosity(*pos):
        return 0.1

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
        perm=get_k, heat_cond=2.0
    )
    model = seepage.create(**opts)
    return model


def show(model: Seepage, jx, jz, caption=None):
    angles = np.linspace(0, np.pi * 2, 100)
    c1 = item('xy', np.cos(angles) * 50 + 150, np.sin(angles) * 50 + 100, 'r--', linewidth=0.5)
    c2 = item('xy', [130, 130], [10, 490], 'k--', linewidth=0.5)
    c3 = item('xy', [170, 170], [10, 490], 'k--', linewidth=0.5)
    show_2d_v2(
        model, dim0=0, dim1=2, shape=[jx, jz], caption=caption, other_items=[c1, c2, c3]
    )


def main():
    jx, jz = 150, 250
    model = create(jx, jz)
    seepage.solve(model=model, extra_plot=lambda: show(model, jx, jz), step_max=10000)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
