import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium._create import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui


"""
水平一注一采纯水模型初版

本阶段目的：
1. 暂时不考虑 He / N2 / CH4；
2. 暂时不考虑脱溶；
3. 暂时不考虑 Reaktoro；
4. 只验证水平一注一采下的压力场、温度场、注采关系是否合理；
5. 为后续加入 He(aq)、N2(aq)、CH4(aq) 被动运移和脱溶模型做基础。

模型解释：
1. x 方向为水平井间方向；
2. z 方向也解释为水平面内的第二个方向，不再代表深度；
3. y 方向为单位厚度方向，同时用于放置虚拟井网格；
4. 因为是水平模型，所以关闭重力 gravity=[0, 0, 0]；
5. 初始压力统一设为 20 MPa，不再使用静水压力；
6. 初始温度统一设为 400 K，不再使用地温梯度。
"""


def create_model():

    mesh = create_xy(
        x_min=0.0, dx=10.0, x_max=1000.0, y_min=0.0, dy=10.0, y_max=1000.0,
        z_min=-0.5, z_max=0.5,

    )

    y_min, y_max = get_pos_range(mesh, 1)
    x_min, x_max = get_pos_range(mesh, 0)


    # ================= 1. 网格体积分配 =================
    # 右侧采出井：保持定压，保留巨大的虚拟体积
    add_cell_face(mesh, pos=[700, (y_min + y_max) / 2, 0.0],offset=[0,0,10],
                  vol=1.0e10, area=2.104, length=1)

    # 左侧注入井：定流量注水
    add_cell_face(mesh, pos=[300, (y_min + y_max) / 2, 0.0], offset=[0,0,-10],

                  vol=100, area=2.104, length=1)


    """
    area 是井-储层连接面积；
    length 是虚拟井网格中心到储层网格中心之间的等效连接距离；
    这里仍然采用等效井连接方式，不直接建立真实井筒几何。

    注意：
    1. 本阶段只是纯水一注一采底座；
    2. 后续如果要解释真实产量，需要对 area、length、虚拟井体积做敏感性分析；
    3. 生产井产水量应通过生产井连接面通量计算，不能直接用虚拟井网格水量变化代表。
    """

    # ============================================================
    # 3. 储层物性
    # ============================================================

    def get_perm(x, y, z):
        # 第一版使用均质渗透率，不加入随机场和低渗夹层
        return 1.0e-14

    def get_s(x, y, z):
        # 当前阶段为纯水模型。
        # 因为调用的是 geothermal_helium._create.create，
        # 所以保留 he_sol 和 n2_sol 作为零含量占位。
        return dict(
            h2o=1.0,
            he_sol=0.0,
            n2_sol=0.0
        )

    def get_denc(x, y, z):
        # 统一体积热容参数。
        # 第一版不设置顶部/底部无限大热容边界。
        return 2.0e6

    def get_porosity(x, y, z):
        return 0.3


    def get_p(x, y, z):
        if z > 2.0:
            # 生产井虚拟网格：低压定压边界
            return 18.0e6
        else:
            # 储层和注入井虚拟网格：统一初始压力
            return 20.0e6

    def get_t(x, y, z):
        if z < -2.0:
            # 注入井虚拟网格初始温度可设为注入水温度
            return 300
        else:
            # 储层和生产井虚拟网格初始温度
            return 400

    # ============================================================
    # 5. 定义官方注入器
    # ============================================================

    my_injectors = [
        {
            "pos":  [300, (y_min + y_max) / 2,-10 ],
            "fluid_id": "h2o",
            "value": 1.3e-4,    ###单位为m³/s
        }
    ]

    # ============================================================
    # 6. 创建模型
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
        dt_max=3600.0 * 24.0 * 1.0,     # 初版最大时间步先设为 1 天
        injectors=my_injectors
    )

    return model


def main():
    from zmlx.scen.geothermal_helium.exsolve.show import show_xy
    model = create_model()
    tfc.solve(
        model=model,
        extra_plot=lambda: show_xy(model),
    )


if __name__ == '__main__':
    gui.execute(main)