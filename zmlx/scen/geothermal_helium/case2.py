import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium._create import create
from zmlx.seepage_mesh import create_xz, add_cell_face
from zmlx.ui import gui


def create_model():
    mesh = create_xz(x_min=0, dx=10, x_max=1000, y_min=-0.5, y_max=0.5,
                     z_min=-2200.0, dz=10, z_max=-1800)

    z_min, z_max = get_pos_range(mesh, 2)
    x_min, x_max = get_pos_range(mesh, 0)

    # ================= 1. 网格体积分配 =================
    # 右侧采出井：保持定压，保留巨大的虚拟体积
    add_cell_face(mesh, pos=[700, 0.0, (z_min + z_max) / 2], offset=[0, 10, 0],
                  vol=1.0e10, area=2.104, length=1)
    """
    接触面积先按照1
    假设单元1*1，2*2，中间0.1m粗井眼，0.1井眼向四周蔓延，达西定律，等效面积应该多大？
    井眼的射孔。
    不同井间距下氦气的采出量？温度或者压力的变化？
    不同注水温度下氦气的采出量？温度或者压力的变化？
    射孔段长度？这个应该也可以设置。
    注采平衡？
    如何输出采出量？
    如果热突破时间是50年，注采平衡的状态下，井间距是281.3m，但是现在注采应该是不平衡的。
    """
    # 左侧注入井：定流量注水
    add_cell_face(mesh, pos=[300, 0.0, (z_min + z_max) / 2], offset=[0, -10, 0],
                  vol=1, area=2.104, length=1)
    """井筒半径为0.1m，体积应该为3.14*0.05*0.05*10=0.0785"""

    def is_upper(x, y, z):
        return abs(z - z_max) < 100

    def is_lower(x, y, z):
        return abs(z - z_min) < 100

    def get_perm(x, y, z):
        return 1.0e-18 if is_upper(x, y, z) or is_lower(x, y, z) else 1.0e-12

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
            return 2e6

    def get_porosity(x, y, z):
        return 0.3

    # ================= 2. 初始压力与温度 =================
    def get_p(x, y, z):
        if y > 2:
            return 18e6  # 右侧采出井：维持定压 18 MPa
        else:
            return -1e4 * z  # 左侧注入井与中间地层：维持自然静水压，等待注水憋高

    def get_t(x, y, z):
        if y < -2:
            return 313.15  # 左侧注入井：313K 冷水
        else:
            return 293.15 - 0.035 * z

    # ================= 3. 定义官方注入器 =================
    my_injectors = [
        {
            "pos": [300, -10, (z_min + z_max) / 2],
            "fluid_id": "h2o" ,
            "value":0.0017,
        }
    ]
    """注入流量与射孔段长度有关,射孔段不存在，假设射孔段为300m？均摊到每个网格为0.0025kg/s。但是吧这个射孔段长度一般来说设置为多少？
    300米？"""
    # ================= 4. 创建模型 =================
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
        dt_max=3600.0 * 24.0 * 100.0,
        gravity=[0, 0, -10],
        injectors=my_injectors  # <--- 将注入器字典交给官方接口
    )

    return model


def main():
    from zmlx.scen.geothermal_helium._show import show_xz
    model = create_model()
    tfc.solve(model=model, extra_plot=lambda: show_xz(model))


if __name__ == '__main__':
     gui.execute(main)
