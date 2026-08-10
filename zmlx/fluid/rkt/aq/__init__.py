"""基于 Reaktoro 的气体-水溶液密度计算.

气-液两相平衡下的水溶液密度。通过 EquilibriumSolver 自动将气体
在气相和水相之间分配，低于饱和溶解度时全部溶解，超过时水相为饱和态。

    导入:   from zmlx.fluid.rkt.aq import h2o_ch4_density
    调用:   rho = h2o_ch4_density(w=0.001, P=10e6, T=300)  # → kg/m³
    溶解度: w_sat = h2o_ch4_solubility(P=10e6, T=300)
    绘图:   python -m zmlx.fluid.rkt.aq._ch4

气体列表（溶解度从低到高）
--------------------------
    H2      h2o_h2_density / h2o_h2_solubility         极低
    He      h2o_he_density / h2o_he_solubility         极低
    CH4     h2o_ch4_density / h2o_ch4_solubility       低
    N2      h2o_n2_density / h2o_n2_solubility         低
    O2      h2o_o2_density / h2o_o2_solubility         中
    CO2     h2o_co2_density / h2o_co2_solubility       高（化学反应增溶）

绘图
----
    from zmlx.fluid.rkt.aq._plot import plot_density_ratio
    plot_density_ratio("CH4", h2o_ch4_density, w_max=0.003, fn_solubility=h2o_ch4_solubility)
"""

try:
    from zmlx.fluid.rkt.aq._ch4 import h2o_ch4_density, h2o_ch4_solubility
    from zmlx.fluid.rkt.aq._co2 import h2o_co2_density, h2o_co2_solubility
    from zmlx.fluid.rkt.aq._h2 import h2o_h2_density, h2o_h2_solubility
    from zmlx.fluid.rkt.aq._he import h2o_he_density, h2o_he_solubility
    from zmlx.fluid.rkt.aq._n2 import h2o_n2_density, h2o_n2_solubility
    from zmlx.fluid.rkt.aq._o2 import h2o_o2_density, h2o_o2_solubility
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        f"{e}\n\nReaktoro 未安装，请运行:  conda install -c conda-forge reaktoro"
    ) from e


from zmlx.fluid.rkt.aq._create_gas_aqueous import create_gas_aqueous