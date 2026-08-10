"""Reaktoro 流体物性的 T-P 云图绘制.

提供 plot_contours 函数，生成密度和比热的等值线图。
通过 zmlx.ui.plot 自动适配 GUI / 无 GUI 环境，支持暗色模式等值线颜色切换。
"""

import numpy as np


def plot_contours(label, fn_density, fn_specific_heat=None,
                  t_range=(280, 500), p_range=(1e5, 30e6),
                  n_t=23, n_p=21):
    """绘制流体密度和比热的 T-P 云图.

    布局：第一行为密度，第二行为比热（可选）。
    每行左侧为填充图 (contourf)，右侧为等值线 (contour)。

    Args:
        label: 流体名称（如 'CH4'）
        fn_density: 密度函数 fn(P, T) → kg/m³
        fn_specific_heat: 定压比热函数 fn(P, T) → J/(kg·K)（可选）
        t_range: 温度范围 (T_min, T_max) (K)
        p_range: 压力范围 (P_min, P_max) (Pa)
        n_t: 温度采样点数
        n_p: 压力采样点数
    """

    Ts = np.linspace(*t_range, n_t)
    Ps = np.linspace(*p_range, n_p)
    TT, PP = np.meshgrid(Ts, Ps)

    def _grid(fn):
        ZZ = np.empty_like(TT)
        for i in range(len(Ps)):
            for j in range(len(Ts)):
                ZZ[i, j] = fn(PP[i, j], TT[i, j])
        return ZZ

    ZZ_d = _grid(fn_density)
    ZZ_c = _grid(fn_specific_heat) if fn_specific_heat is not None else None

    rows = 1 + (1 if ZZ_c is not None else 0)

    def on_figure(fig):
        from zmlx.ui import gui

        lc = "white" if (gui.exists() and gui.in_dark_mode()) else "black"

        axes = fig.subplots(rows, 2)
        if rows == 1:
            axes = axes.reshape(1, 2)

        # ---- 密度 ----
        ax = axes[0, 0]
        cf = ax.contourf(TT, PP / 1e6, ZZ_d, levels=20, cmap="plasma")
        fig.colorbar(cf, ax=ax, label="Density (kg/m^3)")
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Pressure (MPa)")
        ax.set_title(f"{label} Density (Reaktoro)")

        ax = axes[0, 1]
        cs = ax.contour(TT, PP / 1e6, ZZ_d, levels=15, colors=lc, linewidths=0.6)
        ax.clabel(cs, inline=True, fontsize=7)
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Pressure (MPa)")
        ax.set_title(f"{label} Density contours (kg/m^3)")

        # ---- 比热 ----
        if ZZ_c is not None:
            ax = axes[1, 0]
            cf = ax.contourf(TT, PP / 1e6, ZZ_c, levels=20, cmap="cividis")
            fig.colorbar(cf, ax=ax, label="Specific heat (J/(kg.K))")
            ax.set_xlabel("Temperature (K)")
            ax.set_ylabel("Pressure (MPa)")
            ax.set_title(f"{label} Specific heat (Reaktoro)")

            ax = axes[1, 1]
            cs = ax.contour(TT, PP / 1e6, ZZ_c, levels=15, colors=lc, linewidths=0.6)
            ax.clabel(cs, inline=True, fontsize=7)
            ax.set_xlabel("Temperature (K)")
            ax.set_ylabel("Pressure (MPa)")
            ax.set_title(f"{label} Specific heat contours (J/(kg.K))")

        fig.tight_layout()

    from zmlx.ui import plot

    plot(on_figure, caption=f"{label} (Reaktoro)")
