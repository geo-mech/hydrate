# -*- coding: utf-8 -*-

from zmlx import tfc, Seepage, plt


def show_xy(model: Seepage):
    """
    xy平面显示函数。

    显示内容：
    1. 压力场；
    2. 温度场；
    3. 溶解态氦气he_sol质量分数；
    4. 溶解态氦气he_sol质量浓度。
    """

    # ========================================================
    # 0. 基本参数
    # ========================================================

    # 用于从质量分数近似换算质量浓度
    RHO_WATER = 1000.0       # kg/m3

    # 只选择真实储层，不包含外置虚拟井网格
    mask = tfc.get_cell_mask(
        model,
        zr=[-1.0, 1.0]
    )

    # ========================================================
    # 1. 提取坐标和基础物理场
    # ========================================================

    x = tfc.get_x(
        model,
        mask=mask
    )

    y = tfc.get_y(
        model,
        mask=mask
    )

    p = tfc.get_p(
        model,
        mask=mask
    )

    t = tfc.get_t(
        model,
        mask=mask
    )

    # ========================================================
    # 2. 提取水和溶解态氦气质量
    # ========================================================

    h2o_mass = tfc.get_m(
        model,
        fid="h2o",
        mask=mask
    )

    he_mass = tfc.get_m(
        model,
        fid="he_sol",
        mask=mask
    )

    # ========================================================
    # 3. 计算液相总质量
    # ========================================================

    liq_mass = []

    for mh2o, mhe in zip(h2o_mass, he_mass):
        liq_mass.append(
            mh2o + mhe
        )

    # ========================================================
    # 4. 计算氦气质量分数
    # ========================================================

    he_frac = []

    for mhe, mliq in zip(he_mass, liq_mass):
        if mliq > 0.0:
            he_frac.append(
                mhe / mliq
            )
        else:
            he_frac.append(0.0)

    # ========================================================
    # 5. 计算氦气质量浓度
    # ========================================================

    he_conc = []

    for mhe, mliq in zip(he_mass, liq_mass):
        if mliq > 0.0:
            # 液相体积近似：
            # V_liq = m_liq / rho_water
            #
            # 氦气浓度：
            # C_He = m_He / V_liq
            #      = m_He × rho_water / m_liq
            he_conc.append(
                mhe * RHO_WATER / mliq
            )
        else:
            he_conc.append(0.0)

    # ========================================================
    # 6. 压力场
    # ========================================================

    def f_p(fig):
        ax = plt.add_axes2(
            fig,
            aspect="equal",
            xlabel="x (m)",
            ylabel="y (m)",
            title="Pressure Field"
        )

        plt.add_tricontourf(
            ax,
            x,
            y,
            p / 1.0e6,
            cbar={
                "label": "Pressure (MPa)"
            }
        )

    # ========================================================
    # 7. 温度场
    # ========================================================

    def f_t(fig):
        ax = plt.add_axes2(
            fig,
            aspect="equal",
            xlabel="x (m)",
            ylabel="y (m)",
            title="Temperature Field"
        )

        plt.add_tricontourf(
            ax,
            x,
            y,
            t,
            cbar={
                "label": "Temperature (K)"
            }
        )

    # ========================================================
    # 8. 溶解态氦气质量分数场
    # ========================================================

    def f_he_fraction(fig):
        ax = plt.add_axes2(
            fig,
            aspect="equal",
            xlabel="x (m)",
            ylabel="y (m)",
            title="He_sol Mass Fraction"
        )

        plt.add_tricontourf(
            ax,
            x,
            y,
            he_frac,
            cbar={
                "label": "He_sol mass fraction"
            }
        )

    # ========================================================
    # 9. 溶解态氦气质量浓度场
    # ========================================================

    def f_he_concentration(fig):
        ax = plt.add_axes2(
            fig,
            aspect="equal",
            xlabel="x (m)",
            ylabel="y (m)",
            title="He_sol Concentration"
        )

        plt.add_tricontourf(
            ax,
            x,
            y,
            he_conc,
            cbar={
                "label": "He_sol concentration (kg/m3-water)"
            }
        )

    # ========================================================
    # 10. 添加到ZMLX图形显示面板
    # ========================================================

    plt.plot_on_figure(
        f_p,
        caption="Pressure"
    )

    plt.plot_on_figure(
        f_t,
        caption="Temperature"
    )

    plt.plot_on_figure(
        f_he_fraction,
        caption="He Mass Fraction"
    )

    plt.plot_on_figure(
        f_he_concentration,
        caption="He Concentration"
    )