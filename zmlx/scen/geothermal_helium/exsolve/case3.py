# -*- coding: utf-8 -*-

import zmlx.tfc as tfc
from zmlx.exts import get_pos_range
from zmlx.scen.geothermal_helium.exsolve.fluid import create
from zmlx.seepage_mesh import create_xy, add_cell_face
from zmlx.ui import gui


"""
水平一注一采溶解气体被动运移模型：简洁版

本阶段目的：
1. 在第一阶段纯水一注一采模型已经验证稳定的基础上，加入溶解气体组分；
2. 暂时不考虑脱溶；
3. 暂时不考虑 Reaktoro；
4. 暂时不使用亨利定律；
5. 只验证 He(aq)、N2(aq)、CH4(aq) 是否能随水相从储层向生产井被动运移；
6. 通过 show_xy 显示压力、温度和三种溶解气体运移图（mass为单个网格的质量）。
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
# 2. 溶解气体初始含量
# ============================================================

# 注意：
# 这里只是被动运移测试值，不代表真实地层数据。
# 后续如果使用真实地层水数据，需要替换为实测数据换算值。
HE_INIT = 1.0e-6
N2_INIT = 8.0e-4
CH4_INIT = 1.0e-4


def create_model():

    mesh = create_xy(
        x_min=0.0, dx=10.0, x_max=1000.0,
        y_min=0.0, dy=10.0, y_max=1000.0,
        z_min=-0.5, z_max=0.5,
    )

    y_min, y_max = get_pos_range(mesh, 1)
    y_mid = (y_min + y_max) / 2.0

    # ================= 1. 网格体积分配 =================

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
    5. 只有真实储层初始含有溶解气体。
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

        # --------------------------------------------------------
        # 生产井虚拟网格：纯水
        # 注意：
        # 这里不是给生产井设置气体初始浓度；
        # 这里是为了避免生产井误用储层初始气体浓度。
        # --------------------------------------------------------
        elif z > 2.0:
            return dict(
                h2o=1.0,
                he_sol=0.0,
                n2_sol=0.0,
                ch4_sol=0.0
            )

        # --------------------------------------------------------
        # 真实储层：根据测试模式设置初始溶解气体
        # --------------------------------------------------------
        else:

                return dict(
                    h2o=1.0 - HE_INIT - N2_INIT - CH4_INIT,
                    he_sol=HE_INIT,
                    n2_sol=N2_INIT,
                    ch4_sol=CH4_INIT
                )

        raise ValueError(f"未知 TEST_MODE: {TEST_MODE}")

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
        injectors=my_injectors
    )

    return model


def main():
    from zmlx.scen.geothermal_helium.exsolve.show2 import show_xy

    model = create_model()

    tfc.solve(
        model=model,
        extra_plot=lambda: show_xy(model),
    )


if __name__ == '__main__':
    gui.execute(main)