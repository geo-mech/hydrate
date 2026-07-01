# -*- coding: utf-8 -*-

from zmlx import tfc, Seepage, plt


def show_xy(model: Seepage):
    """
    xy 平面显示函数。

    显示内容：
    1. 压力场；
    2. 温度场；
    3. He / N2 / CH4 质量分数分布；
    4. He / N2 / CH4 浓度分布。

    注意：
    1. 本函数只显示真实储层平面，即 z 在 [-1, 1] 内的网格；
    2. 不显示 z < -2 的注入井虚拟网格；
    3. 不显示 z > 2 的生产井虚拟网格；
    4. 质量分数 = 组分质量 / 液相总质量；
    5. 浓度近似按 C = 组分质量 / 液相体积 计算；
    6. 液相体积近似为 液相总质量 / 1000 kg/m3。
    """

    # ============================================================
    # 0. 基本参数
    # ============================================================

    RHO_WATER = 1000.0  # kg/m3，用于估算水相体积

    # 只显示真实储层，不显示外置虚拟井网格
    mask = tfc.get_cell_mask(model, zr=[-1, 1])

    ca = tfc.cell_keys(model)

    # ============================================================
    # 1. 提取坐标与基础物理场
    # ============================================================

    x = tfc.get_x(model, mask=mask)
    y = tfc.get_y(model, mask=mask)

    p = tfc.get_p(model, mask=mask)
    t = tfc.get_t(model, mask=mask)

    # ============================================================
    # 2. 安全读取质量
    # ============================================================

    def safe_get_m(fid):
        """
        安全读取某个组分的质量。

        如果当前模型中不存在该组分，则返回全 0。
        这样 2A、2B、2C 模式可以共用同一个 show_xy。
        """
        try:
            return tfc.get_m(model, fid=fid, mask=mask)
        except Exception:
            return [0.0 for _ in x]

    h2o_mass = safe_get_m('h2o')
    he_mass = safe_get_m('he_sol')
    n2_mass = safe_get_m('n2_sol')
    ch4_mass = safe_get_m('ch4_sol')

    # ============================================================
    # 3. 计算液相总质量、质量分数、浓度
    # ============================================================

    liq_mass = []
    for mh, mhe, mn2, mch4 in zip(h2o_mass, he_mass, n2_mass, ch4_mass):
        liq_mass.append(mh + mhe + mn2 + mch4)

    def calc_mass_fraction(comp_mass):
        """
        质量分数：
            X_i = m_i / m_liq
        """
        values = []
        for mc, ml in zip(comp_mass, liq_mass):
            if ml > 0.0:
                values.append(mc / ml)
            else:
                values.append(0.0)
        return values

    def calc_concentration(comp_mass):
        """
        浓度：
            C_i = m_i / V_liq

        其中：
            V_liq ≈ m_liq / rho_water

        所以：
            C_i ≈ m_i * rho_water / m_liq

        单位：
            kg/m3-water
        """
        values = []
        for mc, ml in zip(comp_mass, liq_mass):
            if ml > 0.0:
                values.append(mc * RHO_WATER / ml)
            else:
                values.append(0.0)
        return values

    he_frac = calc_mass_fraction(he_mass)
    n2_frac = calc_mass_fraction(n2_mass)
    ch4_frac = calc_mass_fraction(ch4_mass)

    he_conc = calc_concentration(he_mass)
    n2_conc = calc_concentration(n2_mass)
    ch4_conc = calc_concentration(ch4_mass)

    # ============================================================
    # 4. 基础场绘图
    # ============================================================

    def f_p(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='Pressure Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            p / 1e6,
            cbar=dict(label='Pressure (MPa)')
        )

    def f_t(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='Temperature Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            t,
            cbar=dict(label='Temperature (K)')
        )

    # ============================================================
    # 5. 三种气体质量分数合并图
    # ============================================================

    def f_gas_fraction(fig):
        fig.clear()

        ax1 = fig.add_subplot(1, 3, 1)
        ax1.set_aspect('equal', adjustable='box')
        ax1.set_xlabel('x (m)')
        ax1.set_ylabel('y (m)')
        ax1.set_title('He_sol Mass Fraction')
        plt.add_tricontourf(
            ax1,
            x,
            y,
            he_frac,
            cbar=dict(label='He_sol mass fraction')
        )

        ax2 = fig.add_subplot(1, 3, 2)
        ax2.set_aspect('equal', adjustable='box')
        ax2.set_xlabel('x (m)')
        ax2.set_ylabel('y (m)')
        ax2.set_title('N2_sol Mass Fraction')
        plt.add_tricontourf(
            ax2,
            x,
            y,
            n2_frac,
            cbar=dict(label='N2_sol mass fraction')
        )

        ax3 = fig.add_subplot(1, 3, 3)
        ax3.set_aspect('equal', adjustable='box')
        ax3.set_xlabel('x (m)')
        ax3.set_ylabel('y (m)')
        ax3.set_title('CH4_sol Mass Fraction')
        plt.add_tricontourf(
            ax3,
            x,
            y,
            ch4_frac,
            cbar=dict(label='CH4_sol mass fraction')
        )

        fig.suptitle('Dissolved Gas Mass Fraction Field')
        fig.tight_layout()

    # ============================================================
    # 6. 三种气体浓度合并图
    # ============================================================

    def f_gas_concentration(fig):
        fig.clear()

        ax1 = fig.add_subplot(1, 3, 1)
        ax1.set_aspect('equal', adjustable='box')
        ax1.set_xlabel('x (m)')
        ax1.set_ylabel('y (m)')
        ax1.set_title('He_sol Concentration')
        plt.add_tricontourf(
            ax1,
            x,
            y,
            he_conc,
            cbar=dict(label='He_sol concentration (kg/m3-water)')
        )

        ax2 = fig.add_subplot(1, 3, 2)
        ax2.set_aspect('equal', adjustable='box')
        ax2.set_xlabel('x (m)')
        ax2.set_ylabel('y (m)')
        ax2.set_title('N2_sol Concentration')
        plt.add_tricontourf(
            ax2,
            x,
            y,
            n2_conc,
            cbar=dict(label='N2_sol concentration (kg/m3-water)')
        )

        ax3 = fig.add_subplot(1, 3, 3)
        ax3.set_aspect('equal', adjustable='box')
        ax3.set_xlabel('x (m)')
        ax3.set_ylabel('y (m)')
        ax3.set_title('CH4_sol Concentration')
        plt.add_tricontourf(
            ax3,
            x,
            y,
            ch4_conc,
            cbar=dict(label='CH4_sol concentration (kg/m3-water)')
        )

        fig.suptitle('Dissolved Gas Concentration Field')
        fig.tight_layout()

    # ============================================================
    # 7. 输出面板区
    # ============================================================

    plt.plot_on_figure(f_p, caption='Pressure')
    plt.plot_on_figure(f_t, caption='Temperature')
    plt.plot_on_figure(f_gas_fraction, caption='Gas Mass Fraction')
    plt.plot_on_figure(f_gas_concentration, caption='Gas Concentration')