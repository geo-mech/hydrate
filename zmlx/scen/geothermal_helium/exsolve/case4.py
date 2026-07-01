import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui
"""
水平一注一采溶解气体被动运移模型：SP2真实数据换算版

本阶段目的：
1. 在纯水一注一采模型基础上加入 He(aq)、N2(aq)、CH4(aq)；
2. 暂时不考虑脱溶；
3. 暂时不考虑 Reaktoro；
4. 暂时不使用亨利定律；
5. 只验证 He(aq)、N2(aq)、CH4(aq) 是否能随水相从储层向生产井被动运移；
6. 使用文献 SP2 气体组成 + 气水比，将数据换算为质量份额；
7. 通过 use_mass=True，使 get_s 返回值按质量份额初始化。
"""


# ============================================================
# 1. 全局参数
# ============================================================

P_INIT = 20.0e6          # 储层初始压力，Pa
P_PROD = 19.8e6          # 生产井虚拟网格初始压力，Pa

T_RES = 400.0            # 储层初始温度，K
T_INJ = 300.0            # 注入水温度，K

PERM_VALUE = 5.0e-13     # 渗透率，m2
POROSITY = 0.3

Q_IN = 1.3e-4            # 注入流量，m3/s
# ============================================================
# 2. SP2 文献数据：气体组成 + 气水比
# ============================================================

# ------------------------------------------------------------
# SP2 气体组成，来自“气体组分分析数据”表
# 注意：这里是伴生气/逸出气中的体积分数，不是水中质量分数
# ------------------------------------------------------------
SP2_HE_Y = 2.240 / 100.0
SP2_N2_Y = 73.800 / 100.0
SP2_CH4_Y = 12.800 / 100.0
# ------------------------------------------------------------
# 三普2号气水比，来自“气水比测量成果数据”表
# ------------------------------------------------------------
SP2_GAS_WATER_RATIO = 24.2 / 100.0


def gas_water_to_mass_fractions(
        gas_water_ratio,
        y_he,
        y_n2,
        y_ch4,
        rho_w=1000.0,
        vm=22.414e-3
):
    """
    将“气水比 + 伴生气组分体积分数”换算为 zmlx use_mass=True 下的初始质量份额。

    参数
    ----
    gas_water_ratio:
        气水比，单位 m3 gas / m3 water。
        例如 24.2% 输入 0.242。

    y_he, y_n2, y_ch4:
        伴生气中 He、N2、CH4 的体积分数。
        例如 He = 2.240% 输入 0.02240。

    rho_w:
        水密度，kg/m3。这里近似取 1000 kg/m3。

    vm:
        气体摩尔体积，m3/mol。
        默认 22.414e-3 m3/mol，即标准状态下 22.414 L/mol。

    返回
    ----
    dict:
        h2o、he_sol、n2_sol、ch4_sol 的质量份额。
        注意：这里不是把 He/N2/CH4 三者归一化到 100%，
        而是把“水 + 三种溶解气体组分”作为整体归一。
    """

    # 摩尔质量，kg/mol
    M_HE = 4.0026e-3
    M_N2 = 28.0134e-3
    M_CH4 = 16.043e-3

    # --------------------------------------------------------
    # 1. 每 1 m3 水对应的各气体标准体积
    # 单位：m3 gas / m3 water
    # --------------------------------------------------------
    V_he = gas_water_ratio * y_he
    V_n2 = gas_water_ratio * y_n2
    V_ch4 = gas_water_ratio * y_ch4

    # --------------------------------------------------------
    # 2. 换算为物质的量
    # 单位：mol / m3 water
    # --------------------------------------------------------
    n_he = V_he / vm
    n_n2 = V_n2 / vm
    n_ch4 = V_ch4 / vm

    # --------------------------------------------------------
    # 3. 换算为质量
    # 单位：kg / m3 water
    # --------------------------------------------------------
    m_he = n_he * M_HE
    m_n2 = n_n2 * M_N2
    m_ch4 = n_ch4 * M_CH4

    # --------------------------------------------------------
    # 4. 换算为 kg gas / kg water
    # --------------------------------------------------------
    r_he = m_he / rho_w
    r_n2 = m_n2 / rho_w
    r_ch4 = m_ch4 / rho_w

    # --------------------------------------------------------
    # 5. 转为 use_mass=True 下的质量份额
    # h2o + he_sol + n2_sol + ch4_sol = 1
    # --------------------------------------------------------
    total = 1.0 + r_he + r_n2 + r_ch4

    result = dict(
        h2o=1.0 / total,
        he_sol=r_he / total,
        n2_sol=r_n2 / total,
        ch4_sol=r_ch4 / total
    )
    return result


# SP2 对应的真实储层初始质量份额
SP2_INIT_S = gas_water_to_mass_fractions(
    gas_water_ratio=SP2_GAS_WATER_RATIO,
    y_he=SP2_HE_Y,
    y_n2=SP2_N2_Y,
    y_ch4=SP2_CH4_Y
)


def create_model():

    mesh = create_xy(
        x_min=0.0, dx=10.0, x_max=1000.0,
        y_min=0.0, dy=10.0, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = (y_min + y_max) / 2.0

    # ============================================================
    # 1. 网格体积分配
    # ============================================================

    # 右侧采出井：生产井虚拟网格外置到 z > 2
    add_cell_face(
        mesh,
        pos=[700, y_mid, 0.0],
        offset=[0, 0, 10],
        vol=1.0e8,
        area=2.104,
        length=1
    )

    # 左侧注入井：注入井虚拟网格外置到 z < -2
    add_cell_face(
        mesh,
        pos=[300, y_mid, 0.0],
        offset=[0, 0, -10],
        vol=100,
        area=2.104,
        length=1
    )

    """
    area 是井-储层连接面积；
    length 是虚拟井网格中心到储层网格中心之间的等效连接距离；
    这里仍然采用等效井连接方式，不直接建立真实井筒几何。

    注意：
    1. 本阶段不是脱溶模型；
    2. He_sol、n2_sol、ch4_sol 只作为水相中的被动组分；
    3. 注入井虚拟网格为纯水；
    4. 生产井虚拟网格为纯水；
    5. 只有真实储层初始含有溶解气体；
    6. 本代码使用 use_mass=True，因此 get_s 返回值按质量份额填充。
    """

    # ============================================================
    # 2. 储层物性
    # ============================================================

    def get_perm(x, y, z):
        # 沿用第一阶段已经验证稳定的均质渗透率
        return PERM_VALUE

    def get_s(x, y, z):
        # --------------------------------------------------------
        # 注入井虚拟网格：纯水
        # --------------------------------------------------------
        if z < -2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )
        elif z > 2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        # --------------------------------------------------------
        # 真实储层：使用 SP2 文献数据换算后的质量份额
        # --------------------------------------------------------
        else:
            return SP2_INIT_S.copy()

    def get_denc(x, y, z):
        # 统一体积热容参数
        return 2.0e6

    def get_porosity(x, y, z):
        return POROSITY

    def get_p(x, y, z):
        if z > 2.0:
            # 生产井虚拟网格初始压力
            return P_PROD
        else:
            # 储层和注入井虚拟网格初始压力
            return P_INIT

    def get_t(x, y, z):
        if z < -2.0:
            # 注入井虚拟网格初始温度设为注入水温度
            return T_INJ
        else:
            # 储层和生产井虚拟网格初始温度
            return T_RES

    # ============================================================
    # 3. 定义官方注入器
    # ============================================================

    my_injectors = [
        {
            "pos": [300, y_mid, -10],
            "fluid_id": "h2o",
            "value": Q_IN,    # 单位按 m3/s 理解
        }
    ]

    # ============================================================
    # 4. 创建模型
    # ============================================================

    model = create(
        mesh=mesh,
        porosity=get_porosity,
        pore_modulus=100.0e6,
        p=get_p,
        temperature=get_t,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.56,
        dist=0.8,
        dt_max=3600.0 * 24.0 * 1.0,
        gravity=[0, 0, 0],
        injectors=my_injectors,
        use_mass=True
    )
    return model
def main():
    from zmlx.scen.geothermal_helium.exsolve.show3 import show_xy

    model = create_model()

    tfc.solve(
        model=model,
        extra_plot=lambda: show_xy(model),
    )

if __name__ == '__main__':
    gui.execute(main)