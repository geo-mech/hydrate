"""基于 Reaktoro 的纯流体物性计算.

使用 Supcrt98 (HKF) 数据库，适用于高温高压地质化学场景。
覆盖 7 种流体，每种提供密度、比热两个函数（不含粘度）。

    导入:   from zmlx.fluid.rkt import h2o_density
    调用:   rho = h2o_density(P=10e6, T=300)   # P(Pa), T(K) → kg/m³
    绘图:   python -m zmlx.fluid.rkt._ch4
    对比:   python -m zmlx.fluid.rkt._compare_rkt_and_cp

与 CoolProp (cp/) 的关系
-------------------------
    Reaktoro 使用 Supcrt98 地质化学数据库（HKF 模型），精度低于 CoolProp
    的 Helmholtz EOS，但支持水溶液多相平衡（见 rkt.aq/）。

    H₂O 和 He 两个引擎高度一致（误差 < 1%），可互换使用。
    对 CO₂ / CH₄ 在近临界区差异显著，工程精度推荐使用 cp/。

流体列表
--------
    H₂O     h2o_density / h2o_specific_heat
    H₂      h2_density  / h2_specific_heat
    He      he_density  / he_specific_heat
    CH₄     ch4_density / ch4_specific_heat
    N₂      n2_density  / n2_specific_heat
    O₂      o2_density  / o2_specific_heat
    CO₂     co2_density / co2_specific_heat

    C₂H₆ 在 Supcrt98 中不可用；如需乙烷请使用 cp/。

绘图
----
    from zmlx.fluid.rkt._plot import plot_contours
    plot_contours("H2O", h2o_density, h2o_specific_heat)
"""

try:
    from zmlx.fluid.rkt._co2 import co2_density, co2_specific_heat
    from zmlx.fluid.rkt._h2 import h2_density, h2_specific_heat
    from zmlx.fluid.rkt._h2o import h2o_density, h2o_specific_heat
    from zmlx.fluid.rkt._he import he_density, he_specific_heat
    from zmlx.fluid.rkt._ch4 import ch4_density, ch4_specific_heat
    from zmlx.fluid.rkt._n2 import n2_density, n2_specific_heat
    from zmlx.fluid.rkt._o2 import o2_density, o2_specific_heat
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        f"{e}\n\nReaktoro 未安装，请运行:  conda install -c conda-forge reaktoro"
    ) from e
