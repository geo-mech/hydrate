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

    # 依然保留这两个虚拟网格作为“井筒缓冲空间”
    add_cell_face(mesh, pos=[700, 0.0, (z_min + z_max) / 2], offset=[0, 10, 0],
                  vol=1.0e10, area=2, length=1)
    add_cell_face(mesh, pos=[300, 0.0, (z_min + z_max) / 2], offset=[0, -10, 0],
                  vol=1.0e10, area=2, length=1)

    def is_upper(x, y, z):
        return abs(z - z_max) < 100

    def is_lower(x, y, z):
        return abs(z - z_min) < 100

    def get_perm(x, y, z):
        return 1.0e-20 if is_upper(x, y, z) or is_lower(x, y, z) else 5.0e-13

    def get_s(x, y, z):
        if y < -2:
            # 左侧注入井边界 (y < -2)：强行注入经过脱气的冷水，不含氦气和氮气
            # 保证地层中抽出的氦气全都是储层原本自带的
            return dict(h2o=1.0, he_sol=0.0, n2_sol=0.0)
        else:
            # 储层及采出井初始状态：基于气水比 2.5:1 和 (N2:98.5%, He:1.5%) 计算的质量分数
            return dict(
                h2o=0.999,
                n2_sol=0.0008,
                he_sol=0.000001
            )


    def get_denc(x, y, z):
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:
            return 1e20
        else:
            return 4e6

    def get_porosity(x, y, z):
        return 0.3

    # ================= 核心修改：恢复驱动压差 =================
    def get_p(x, y, z):
        # 必须有压差水才会流！
        # 地层中心处初始静水压约为 20 MPa (-1e4 * -2000)
        if y < -2:
            return 25e6       # 左侧注入井：强行憋高到 25 MPa
        elif y > 2:
            return 15e6       # 右侧采出井：强行抽低到 15 MPa
        else:
            return -1e4 * z   # 中间地层：维持自然静水压

    def get_t(x, y, z):
        if y < -2:
            return 313.15      # 左侧注入井：注入 313K 冷水
        else:
            return 293.15 - 0.035 * z  # 中间地层与采出井：维持地层高温
    # ==========================================================

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=5e9,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.56,
        dist=0.8,
        has_solid=False,
        dt_max=3600.0 * 24.0 * 30.0,
        gravity=[0, 0, -10]

    )
    return model


def main():
    from zmlx.scen.geothermal_helium._show import show_xz
    model = create_model()
    tfc.solve(model=model, extra_plot=lambda: show_xz(model))


if __name__ == '__main__':
    gui.execute(main)
