import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium._create import create
from zmlx.seepage_mesh import create_xz, add_cell_face
from zmlx.ui import gui

("主要考虑氦气的产出和井位的优化，怎样布井更有利于产氦和采热"
 "改变井的布置"
 "井间距"
 "注入流量变化"
 "是不是也可以考虑氦-氮-甲烷等变化（不同注采深度，生产井压力和射孔段位置？累计产氦量、采热量和热突破时间，有利于地热-氦气协同开发的井位配置）"
 "如果能提出一个比较合适的协同开发的井位布置也可以吧。"
 "U热能固定，输入TP，输出平衡状态TP，局部可以，单元格固定体积和热能？")
def create_model():
    mesh = create_xz(x_min=0, dx=10, x_max=1000, y_min=-0.5, y_max=0.5,
                     z_min=-2200.0, dz=10, z_max=-1800)

    z_min, z_max = get_pos_range(mesh, 2)
    x_min, x_max = get_pos_range(mesh, 0)

    # ================= 1. 网格体积分配 =================
    # 右侧采出井：保持定压，保留巨大的虚拟体积
    add_cell_face(mesh, pos=[700, 0.0, (z_min + z_max) / 2], offset=[0, 10, 0],
                  vol=1.0e10, area=2.104, length=1)

    # 左侧注入井：定流量注水
    add_cell_face(mesh, pos=[300, 0.0, (z_min + z_max) / 2], offset=[0, -10, 0],
                  vol=100, area=2.104, length=1)
    """area是连接面积，L是等效流动距离，L是虚拟井网格中心到储层网格中心之间的等效连接距离，area是这条连接面的等效流通面积
    真实井模型常用Peacman井模型或者井指数来连接井底流压和网格压力，井指数本质上把井几何，储层渗透率、完井长度、等效半径、精通半径和表皮系数等
    因素综合起来。
    """

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
            "value":1.3e-4,    ###单位为m³/s
        }
    ]

    # ================= 4. 创建模型 =================
    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100e6,
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

