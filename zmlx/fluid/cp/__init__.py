"""基于 CoolProp 的纯流体物性计算.

使用 Helmholtz 能量状态方程，对标 NIST REFPROP，误差 < 0.1%。
覆盖 8 种流体，每种提供密度、粘度、比热三个函数。

    导入:   from zmlx.fluid.cp import h2o_density
    调用:   rho = h2o_density(P=10e6, T=300)   # P(Pa), T(K) → kg/m³
    绘图:   python -m zmlx.fluid.cp._ch4
    对比:   python -m zmlx.fluid.rkt._compare_rkt_and_cp

流体列表
--------
    H₂O     Water        h2o_density / h2o_viscosity / h2o_specific_heat
    H₂      Hydrogen     h2_density  / h2_viscosity  / h2_specific_heat
    He      Helium       he_density  / he_viscosity  / he_specific_heat
    CH₄     Methane      ch4_density / ch4_viscosity / ch4_specific_heat
    C₂H₆    Ethane       c2h6_density/ c2h6_viscosity/ c2h6_specific_heat
    N₂      Nitrogen     n2_density  / n2_viscosity  / n2_specific_heat
    O₂      Oxygen       o2_density  / o2_viscosity  / o2_specific_heat
    CO₂     CO2          co2_density / co2_viscosity / co2_specific_heat

绘图
----
    from zmlx.fluid.cp._plot import plot_contours
    plot_contours("CH4", ch4_density, ch4_viscosity, ch4_specific_heat)
"""

try:
    from zmlx.fluid.cp._c2h6 import c2h6_density, c2h6_specific_heat, c2h6_viscosity
    from zmlx.fluid.cp._co2 import co2_density, co2_specific_heat, co2_viscosity
    from zmlx.fluid.cp._h2 import h2_density, h2_specific_heat, h2_viscosity
    from zmlx.fluid.cp._h2o import h2o_density, h2o_specific_heat, h2o_viscosity
    from zmlx.fluid.cp._he import he_density, he_specific_heat, he_viscosity
    from zmlx.fluid.cp._ch4 import ch4_density, ch4_specific_heat, ch4_viscosity
    from zmlx.fluid.cp._n2 import n2_density, n2_specific_heat, n2_viscosity
    from zmlx.fluid.cp._o2 import o2_density, o2_specific_heat, o2_viscosity
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        f"{e}\n\nCoolProp 未安装，请运行:  pip install CoolProp\n"
        f"CoolProp is not installed. Run: pip install CoolProp"
    ) from e

from zmlx.fluid.cp._create_fludef import create_fludef
