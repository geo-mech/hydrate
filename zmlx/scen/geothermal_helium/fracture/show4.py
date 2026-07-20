# -*- coding: utf-8 -*-

from zmlx import tfc, Seepage, plt


def show_xy(model: Seepage):
    """
    xy 平面显示函数。

    显示内容：
    1. 压力场；
    2. 温度场；
    3. He / N2 / CH4 质量分数分布；
    4. He / N2 / CH4 浓度分布；
    5. 在所有图上叠加裂缝网络位置。

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
    # 0.1 读取裂缝网络和井位信息
    # ============================================================

    def get_temp_value(key, default=None):
        """
        安全读取 model.temps 中的值。
        """
        try:
            return model.temps[key]
        except Exception:
            return default

    def get_fracture_segments():
        """
        从 model.temps 中读取裂缝几何。
        支持：
        1. fracture_records: [{'geometry':[x0,y0,x1,y1], ...}, ...]
        2. fracture_geometry: [x0, y0, x1, y1]
        """
        segments = []

        fracture_records = get_temp_value("fracture_records", [])
        if fracture_records is not None and len(fracture_records) > 0:
            for record in fracture_records:
                try:
                    geom = record.get("geometry", None)
                    if geom is not None and len(geom) == 4:
                        segments.append(geom)
                except Exception:
                    pass

        if len(segments) == 0:
            geom = get_temp_value("fracture_geometry", None)
            if geom is not None and len(geom) == 4:
                segments.append(geom)

        return segments

    fracture_segments = get_fracture_segments()

    # 如果你在建模代码中保存了井位，这里也会自动叠加
    injector_xy = get_temp_value("injector_xy", None)
    producer_xy = get_temp_value("producer_xy", None)

    def add_fracture_overlay(ax):
        """
        在已有坐标轴上叠加裂缝网络和井位。
        """
        has_label = False

        # 叠加裂缝
        for i, seg in enumerate(fracture_segments):
            try:
                x0, y0, x1, y1 = seg
            except Exception:
                continue

            label_line = "Fracture" if i == 0 else None
            label_end = "Fracture endpoints" if i == 0 else None

            ax.plot(
                [x0, x1],
                [y0, y1],
                linewidth=2.5,
                linestyle='-',
                zorder=20,
                label=label_line
            )

            ax.scatter(
                [x0, x1],
                [y0, y1],
                s=18,
                zorder=21,
                label=label_end
            )

            # 裂缝编号
            xc = 0.5 * (x0 + x1)
            yc = 0.5 * (y0 + y1)
            ax.text(
                xc, yc, f'F{i + 1}',
                fontsize=9,
                zorder=22
            )

            has_label = True

        # 叠加井位
        if injector_xy is not None and len(injector_xy) >= 2:
            ax.scatter(
                [injector_xy[0]],
                [injector_xy[1]],
                marker='^',
                s=80,
                zorder=23,
                label='Injector'
            )
            has_label = True

        if producer_xy is not None and len(producer_xy) >= 2:
            ax.scatter(
                [producer_xy[0]],
                [producer_xy[1]],
                marker='s',
                s=70,
                zorder=23,
                label='Producer'
            )
            has_label = True

        if has_label:
            try:
                ax.legend(loc='best', fontsize=8)
            except Exception:
                pass

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
        add_fracture_overlay(ax)

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
        add_fracture_overlay(ax)

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
        add_fracture_overlay(ax1)

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
        add_fracture_overlay(ax2)

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
        add_fracture_overlay(ax3)

        fig.suptitle('Dissolved Gas Mass Fraction Field')
        fig.tight_layout(rect=[0, 0, 1, 0.96])

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
        add_fracture_overlay(ax1)

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
        add_fracture_overlay(ax2)

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
        add_fracture_overlay(ax3)

        fig.suptitle('Dissolved Gas Concentration Field')
        fig.tight_layout(rect=[0, 0, 1, 0.96])

    # ============================================================
    # 7. 输出面板区
    # ============================================================

    plt.plot_on_figure(f_p, caption='Pressure')
    plt.plot_on_figure(f_t, caption='Temperature')
    plt.plot_on_figure(f_gas_fraction, caption='Gas Mass Fraction')
    plt.plot_on_figure(f_gas_concentration, caption='Gas Concentration')