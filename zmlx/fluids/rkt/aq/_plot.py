"""水溶液密度比值绘图.

提供 plot_density_ratio 函数，绘制 ρ/ρ₀ 随质量分数的变化曲线，
自动显示溶解度饱和拐点。
"""

import numpy as np


def plot_density_ratio(label, fn, w_max, P=10.0e6, T=300.0,
                       n=51, color="steelblue", fn_solubility=None):
    """绘制气体-水溶液密度比值随质量分数的变化.

    横轴为气体质量分数 w，纵轴为溶液密度与纯水密度的比值 ρ/ρ₀。
    ρ₀ 值标注于标题中，灰色参考线位于 1.0。

    Args:
        label: 气体名称（如 'CH4'）
        fn: 密度函数 fn(w, P, T) → kg/m³
        w_max: 质量分数上限（根据各气体溶解度不同调整）
        P: 压力 (Pa)，默认 10 MPa
        T: 温度 (K)，默认 300 K
        n: 采样点数
        color: 曲线颜色
        fn_solubility: 溶解度函数 fn(P, T) → w_sat（可选，传入后在标题中显示）
    """

    ws = np.linspace(0, w_max, n)
    rhos = [fn(w, P=P, T=T) for w in ws]

    for w, rho in zip(ws[::max(1, n // 10)], rhos[::max(1, n // 10)]):
        print(f"  w = {w:.5f}  ->  rho = {rho:.2f} kg/m3")

    rho0 = rhos[0]
    ratios = [r / rho0 for r in rhos]

    # 溶解度
    w_sat_text = ""
    if fn_solubility is not None:
        try:
            w_sat = fn_solubility(P=P, T=T)
            w_sat_text = f" (solubility w_sat = {w_sat:.4f})"
        except Exception:
            pass

    def on_figure(fig):
        from zmlx.ui import gui

        ref_color = "gray" if not gui.exists() or not gui.in_dark_mode() else "lightgray"

        ax = fig.add_subplot(111)
        ax.plot(ws, ratios, "o-", markersize=3, color=color)
        ax.axhline(y=1.0, color=ref_color, linestyle="--", linewidth=0.8)
        ax.set_xlabel(f"{label} mass fraction w")
        ax.set_ylabel("Density ratio (rho / rho_0)")
        ax.set_title(f"H2O-{label} aqueous solution density ratio "
                     f"(rho_0 = {rho0:.2f} kg/m^3){w_sat_text}\n"
                     f"T = {T} K, P = {P / 1e6:.0f} MPa")
        ax.grid(True, alpha=0.3)

    from zmlx.ui import plot

    plot(on_figure, caption=f"H2O-{label}")
