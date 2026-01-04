import zmlx.tfc as tfc
from zmlx.alg import get_pos_range
from zmlx.scen.geothermal_helium._create import create
from zmlx.seepage_mesh import create_xz, add_cell_face
from zmlx.ui import gui


def create_model():
    mesh = create_xz(x_min=0, dx=10, x_max=1000, y_min=-0.5, y_max=0.5,
                     z_min=-2200.0, dz=10, z_max=-1800)

    z_min, z_max = get_pos_range(mesh, 2)
    x_min, x_max = get_pos_range(mesh, 0)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[x_max, 0.0, (z_min + z_max) / 2], offset=[0, 10, 0],
                  vol=1.0e10, area=1, length=1)

    def is_upper(x, y, z):
        return abs(z - z_max) < 100

    def is_lower(x, y, z):
        return abs(z - z_min) < 100

    def get_perm(x, y, z):
        return 1.0e-18 if is_upper(x, y, z) or is_lower(x, y, z) else 1.0e-14

    def get_s(x, y, z):
        return dict(h2o=0.99, he_sol=0.005, n2_sol=0.005)

    def get_denc(x, y, z):
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:
            return 1e20
        else:
            return 4e6

    def get_porosity(x, y, z):  # 孔隙度
        return 0.3

    def get_p(x, y, z):
        if abs(y) < 2:
            return -1e4 * z
        else:
            return 10e6

    def get_t(x, y, z):
        return 300 - 0.04 * z

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.0,
        dist=0.5,
        has_solid=False,
        dt_max=3600.0 * 24.0 * 100.0,
        gravity=[0, 0, -10],
    )
    # 返回模型
    return model


def main():
    from zmlx.scen.geothermal_helium._show import show_xz
    model = create_model()
    tfc.solve(model=model, extra_plot=lambda: show_xz(model))


if __name__ == '__main__':
    gui.execute(main)
