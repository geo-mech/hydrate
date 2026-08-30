"""
水平二维模型通用绘图。

显示内容：
1. 压力场；
2. 温度场；
3. He 质量分数；
4. He 浓度；
5. 单独的裂缝网络图。
"""

from zmlx import tfc, Seepage, plt


RANDOM_FRACTURE_LINE_WIDTH = 0.6
MAIN_CHANNEL_LINE_WIDTH = 2.0


def show_xy(model: Seepage):
    """绘制 xy 平面的压力、温度、He 场和裂缝网络。"""

    rho_water = 1000.0
    mask = tfc.get_cell_mask(model, zr=[-1, 1])

    def get_temp_value(key, default=None):
        try:
            return model.temps[key]
        except Exception:
            return default

    fracture_records = get_temp_value("fracture_records", []) or []

    x = tfc.get_x(model, mask=mask)
    y = tfc.get_y(model, mask=mask)
    p = tfc.get_p(model, mask=mask)
    t = tfc.get_t(model, mask=mask)

    def safe_get_m(fid):
        try:
            return tfc.get_m(model, fid=fid, mask=mask)
        except Exception:
            return [0.0 for _ in x]

    # 仅保留 h2o 和 he_sol
    h2o_mass = safe_get_m("h2o")
    he_mass = safe_get_m("he_sol")

    # 当前只考虑水 + 溶解态 He
    liq_mass = [
        mh + mhe
        for mh, mhe in zip(h2o_mass, he_mass)
    ]

    def calc_mass_fraction(comp_mass):
        return [
            mc / ml if ml > 0.0 else 0.0
            for mc, ml in zip(comp_mass, liq_mass)
        ]

    def calc_concentration(comp_mass):
        return [
            mc * rho_water / ml if ml > 0.0 else 0.0
            for mc, ml in zip(comp_mass, liq_mass)
        ]

    he_frac = calc_mass_fraction(he_mass)
    he_conc = calc_concentration(he_mass)

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
            cbar=dict(label="Pressure (MPa)")
        )

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
            cbar=dict(label="Temperature (K)")
        )

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
            cbar=dict(label="He_sol mass fraction")
        )

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
            cbar=dict(label="He_sol concentration (kg/m3-water)")
        )

    def f_fracture_network(fig):
        fig.clear()
        ax = fig.add_subplot(1, 1, 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x / m")
        ax.set_ylabel("y / m")
        ax.set_title("Fracture Network")

        if len(x) > 0 and len(y) > 0:
            x_min = min(x)
            x_max = max(x)
            y_min = min(y)
            y_max = max(y)
            dx_plot = max(1.0, 0.05 * (x_max - x_min))
            dy_plot = max(1.0, 0.05 * (y_max - y_min))
            ax.set_xlim(x_min - dx_plot, x_max + dx_plot)
            ax.set_ylim(y_min - dy_plot, y_max + dy_plot)

        random_legend_added = False
        main_legend_added = False

        for record in fracture_records:
            try:
                geometry = record.get("geometry")
                if geometry is None or len(geometry) != 4:
                    continue

                x0, y0, x1, y1 = geometry
                source_type = record.get("source_type", "random")
            except Exception:
                continue

            if source_type in ("main_channel", "backbone"):
                linewidth = MAIN_CHANNEL_LINE_WIDTH
                label = None if main_legend_added else "Main channel"
                main_legend_added = True
            else:
                linewidth = RANDOM_FRACTURE_LINE_WIDTH
                label = None if random_legend_added else "Fracture"
                random_legend_added = True

            ax.plot(
                [x0, x1],
                [y0, y1],
                linewidth=linewidth,
                label=label
            )

        if fracture_records:
            try:
                ax.legend(loc="best", fontsize=9)
            except Exception:
                pass

        fig.tight_layout()

    plt.plot_on_figure(f_p, caption="Pressure")
    plt.plot_on_figure(f_t, caption="Temperature")
    plt.plot_on_figure(f_he_fraction, caption="He Mass Fraction")
    plt.plot_on_figure(f_he_concentration, caption="He Concentration")
    plt.plot_on_figure(f_fracture_network, caption="Fracture Network")