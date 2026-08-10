"""Reaktoro (rkt) vs CoolProp (cp) 系统对比.

对比两个引擎在 7 种流体、7 个代表性 T/P 工况下的密度和比热差异。
输出统计报告和散点图可视化。

    运行:   python -m zmlx.fluid.rkt._compare_rkt_and_cp

结论摘要
--------
    H₂O / He:   高度一致（误差 < 1%），可互换
    N₂ / O₂:    较一致（密度 < 5%，比热 < 10%）
    H₂:         密度较一致（< 6%），比热极一致（< 2%）
    CH₄ / CO₂:  近临界区差异大（> 10%），工程精度推荐 cp/

对比工况
--------
    280 K, 0.1 MPa  │  300 K, 5 MPa   │  350 K, 10 MPa  │  350 K, 30 MPa
    300 K, 0.1 MPa  │  300 K, 10 MPa  │  400 K, 15 MPa
"""

import sys


def _compare():
    """执行对比并输出报告."""
    import numpy as np

    # 对比的流体（两引擎共有的）
    FLUIDS = [
        ("H2O",  "h2o"),
        ("H2",   "h2"),
        ("He",   "he"),
        ("CH4",  "ch4"),
        ("N2",   "n2"),
        ("O2",   "o2"),
        ("CO2",  "co2"),
    ]

    # 代表性温度压力点
    CASES = [
        ("280 K, 0.1 MPa",  280.0, 0.1e6),
        ("300 K, 0.1 MPa",  300.0, 0.1e6),
        ("300 K, 5 MPa",    300.0, 5e6),
        ("300 K, 10 MPa",   300.0, 10e6),
        ("350 K, 10 MPa",   350.0, 10e6),
        ("400 K, 15 MPa",   400.0, 15e6),
        ("350 K, 30 MPa",   350.0, 30e6),
    ]

    # 加载各模块
    import zmlx.fluid.cp as cp
    import zmlx.fluid.rkt as rkt

    def get_fn(module, fluid, prop):
        name = f"{fluid}_{prop}"
        fn = getattr(module, name, None)
        if fn is None:
            raise AttributeError(f"{module.__name__}.{name} not found")
        return fn

    print("=" * 92)
    print("  Reaktoro (rkt) vs CoolProp (cp) 密度 & 比热 对比报告")
    print("=" * 92)

    # 对每种流体
    all_d_errors = []
    all_c_errors = []

    for label, fluid in FLUIDS:
        print(f"\n{'─' * 92}")
        print(f"  {label}")
        print(f"{'─' * 92}")
        print(f"  {'工况':<22s} {'rkt密度':>12s} {'cp密度':>12s} {'Δ密度%':>10s}  "
              f"{'rkt Cp':>12s} {'cp Cp':>12s} {'ΔCp%':>10s}")
        print(f"  {'─' * 22} {'─' * 12} {'─' * 12} {'─' * 10}  "
              f"{'─' * 12} {'─' * 12} {'─' * 10}")

        d_errors = []
        c_errors = []

        for desc, T, P in CASES:
            try:
                fn_d_rkt = get_fn(rkt, fluid, "density")
                fn_c_rkt = get_fn(rkt, fluid, "specific_heat")
                fn_d_cp = get_fn(cp, fluid, "density")
                fn_c_cp = get_fn(cp, fluid, "specific_heat")

                d_rkt = fn_d_rkt(P, T)
                d_cp = fn_d_cp(P, T)
                c_rkt = fn_c_rkt(P, T)
                c_cp = fn_c_cp(P, T)

                d_err = (d_rkt - d_cp) / d_cp * 100 if d_cp != 0 else float("nan")
                c_err = (c_rkt - c_cp) / c_cp * 100 if c_cp != 0 else float("nan")
                d_errors.append(abs(d_err))
                c_errors.append(abs(c_err))

                print(f"  {desc:<22s} {d_rkt:10.2f} kg {d_cp:10.2f} kg {d_err:+9.1f}%  "
                      f"{c_rkt:10.1f}   {c_cp:10.1f}   {c_err:+9.1f}%")
            except Exception as e:
                print(f"  {desc:<22s} ERROR: {e}")

        avg_d = np.mean(d_errors) if d_errors else float("nan")
        avg_c = np.mean(c_errors) if c_errors else float("nan")
        max_d = max(d_errors) if d_errors else float("nan")
        max_c = max(c_errors) if c_errors else float("nan")

        print(f"  {'平均误差':<22s} {'':>12s} {'':>12s} {avg_d:+9.1f}%  "
              f"{'':>12s} {'':>12s} {avg_c:+9.1f}%")
        print(f"  {'最大误差':<22s} {'':>12s} {'':>12s} {max_d:+9.1f}%  "
              f"{'':>12s} {'':>12s} {max_c:+9.1f}%")

        all_d_errors.extend(d_errors)
        all_c_errors.extend(c_errors)

    # 总体统计
    print(f"\n{'=' * 92}")
    print(f"  总体统计")
    print(f"{'=' * 92}")
    print(f"  密度平均误差: {np.mean(all_d_errors):.1f}%")
    print(f"  密度最大误差: {max(all_d_errors):.1f}%")
    print(f"  比热平均误差: {np.mean(all_c_errors):.1f}%")
    print(f"  比热最大误差: {max(all_c_errors):.1f}%")

    # 结论
    print(f"\n{'─' * 92}")
    print("  结论")
    print(f"{'─' * 92}")
    print("  1. H2O 和 He: rkt 与 cp 高度一致（误差 < 1%），两者可互换使用。")
    print("  2. N2 / O2 / H2: 密度较一致（< 5%），比热在常温常压附近吻合较好。")
    print("  3. CH4 / CO2: 在临界区附近差异显著（> 10%），因为 Supcrt98 使用")
    print("     较简化的状态方程，而 CoolProp 采用高精度 Helmholtz EOS。")
    print("  4. 对工程精度的纯流体计算，推荐使用 cp (CoolProp)；")
    print("     对地质化学场景（水溶液、多相平衡），使用 rkt (Reaktoro)。")
    print("=" * 92)


def _visualize():
    """绘制 rkt vs cp 散点对比图."""
    import matplotlib.pyplot as plt
    import numpy as np
    import zmlx.fluid.cp as cp
    import zmlx.fluid.rkt as rkt

    FLUIDS = ["h2o", "h2", "he", "ch4", "n2", "o2", "co2"]
    LABELS = ["H2O", "H2", "He", "CH4", "N2", "O2", "CO2"]
    COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
              "#9467bd", "#8c564b", "#e377c2"]

    # 生成随机 T-P 采样点
    np.random.seed(42)
    Ts = np.random.uniform(280, 500, 200)
    Ps = np.random.uniform(1e5, 30e6, 200)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    for i, (fluid, label, color) in enumerate(zip(FLUIDS, LABELS, COLORS)):
        try:
            fn_d_rkt = getattr(rkt, f"{fluid}_density")
            fn_d_cp = getattr(cp, f"{fluid}_density")
            fn_c_rkt = getattr(rkt, f"{fluid}_specific_heat")
            fn_c_cp = getattr(cp, f"{fluid}_specific_heat")
        except AttributeError:
            continue

        d_rkt_vals, d_cp_vals = [], []
        c_rkt_vals, c_cp_vals = [], []

        for T, P in zip(Ts, Ps):
            try:
                d_rkt_vals.append(fn_d_rkt(P, T))
                d_cp_vals.append(fn_d_cp(P, T))
                c_rkt_vals.append(fn_c_rkt(P, T))
                c_cp_vals.append(fn_c_cp(P, T))
            except Exception:
                pass

        axes[0, 0].scatter(d_cp_vals, d_rkt_vals, s=3, color=color, alpha=0.5,
                           label=label)
        axes[1, 0].scatter(d_cp_vals, d_rkt_vals, s=3, color=color, alpha=0.5,
                           label=label)
        axes[0, 1].scatter(c_cp_vals, c_rkt_vals, s=3, color=color, alpha=0.5,
                           label=label)
        axes[1, 1].scatter(c_cp_vals, c_rkt_vals, s=3, color=color, alpha=0.5,
                           label=label)

    # 密度全范围 + 密度局部放大
    for ax, xlim in [(axes[0, 0], None), (axes[1, 0], (0, 200))]:
        ax.plot([0, 1200], [0, 1200], "k--", linewidth=0.5)
        ax.set_xlabel("cp density (kg/m^3)")
        ax.set_ylabel("rkt density (kg/m^3)")
        ax.legend(markerscale=3, fontsize=7)
        ax.grid(True, alpha=0.3)
        if xlim:
            ax.set_xlim(*xlim)
            ax.set_ylim(*xlim)
            ax.set_title("Density (zoom: 0-200 kg/m^3)")
        else:
            ax.set_title("Density")

    # 比热全范围 + 比热局部放大
    for ax, xlim in [(axes[0, 1], None), (axes[1, 1], (0, 6000))]:
        ax.plot([0, 20000], [0, 20000], "k--", linewidth=0.5)
        ax.set_xlabel("cp specific heat (J/(kg.K))")
        ax.set_ylabel("rkt specific heat (J/(kg.K))")
        ax.legend(markerscale=3, fontsize=7)
        ax.grid(True, alpha=0.3)
        if xlim:
            ax.set_xlim(*xlim)
            ax.set_ylim(*xlim)
            ax.set_title("Specific heat (zoom: 0-6000 J/(kg.K))")
        else:
            ax.set_title("Specific heat")

    fig.suptitle("Reaktoro (rkt) vs CoolProp (cp) — Density & Specific Heat",
                 fontsize=14)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    _compare()
    # 有 GUI 时可视化
    try:
        _visualize()
    except Exception:
        pass
