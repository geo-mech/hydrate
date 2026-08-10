"""基于 Reaktoro 溶解度自动创建水溶液 FluDef."""


def create_gas_aqueous(gas, P=10.0e6, T=300.0, h2o=None, name=None):
    """基于气体溶解度创建水溶液 FluDef.

    利用 Reaktoro 计算的气体溶解度和溶液密度，自动确定 create_aqueous
    所需的参数：参考浓度取溶解度的一半，密度倍率由 Reaktoro 计算，
    粘度倍率设为 1.0。

    Args:
        gas: 气体名称（str）或多个气体列表，如 'ch4' 或 ['ch4', 'co2']
        P: 压力 (Pa)，默认 10 MPa
        T: 温度 (K)，默认 300 K
        h2o: 纯水 FluDef（None 则使用 create_h2o 默认值）
        name: 溶液名称（None 则自动生成）

    Returns:
        FluDef: 水溶液定义
    """
    if h2o is None:
        from zmlx.fluid.h2o import create as create_h2o
        h2o = create_h2o(name='H2O(aq)')

    from zmlx.fluid import create_aqueous
    from zmlx.fluid.rkt.aq import (h2o_ch4_density, h2o_ch4_solubility,
                                    h2o_co2_density, h2o_co2_solubility,
                                    h2o_h2_density, h2o_h2_solubility,
                                    h2o_he_density, h2o_he_solubility,
                                    h2o_n2_density, h2o_n2_solubility,
                                    h2o_o2_density, h2o_o2_solubility)

    _gases = {
        'ch4': (h2o_ch4_density, h2o_ch4_solubility),
        'co2': (h2o_co2_density, h2o_co2_solubility),
        'n2': (h2o_n2_density, h2o_n2_solubility),
        'o2': (h2o_o2_density, h2o_o2_solubility),
        'h2': (h2o_h2_density, h2o_h2_solubility),
        'he': (h2o_he_density, h2o_he_solubility),
    }

    if isinstance(gas, str):
        gases = [gas]
    else:
        gases = list(gas)

    solutes = []
    for g in gases:
        g = g.lower()
        if g not in _gases:
            raise ValueError(f"Unknown gas '{g}'. Valid: {list(_gases.keys())}")

        fn_density, fn_solubility = _gases[g]

        w_sat = fn_solubility(P=P, T=T)
        c_ref = w_sat / 2.0

        rho0 = fn_density(0.0, P=P, T=T)
        rho_ref = fn_density(c_ref, P=P, T=T)
        den_times = rho_ref / rho0

        # 线性缩放至 0.05，保证 create_solute 二分搜索收敛
        # 假设密度与浓度线性：(den-1)/c = const
        scale = 0.05 / c_ref
        den_times = 1.0 + (den_times - 1.0) * scale

        sol_name = g.capitalize() if g.isalpha() else g.upper()
        solutes.append([f'{sol_name}(aq)', 0.05, den_times, 1.0])

    if name is None:
        name = 'aq_' + '_'.join(gases)

    return create_aqueous(name=name, h2o=h2o, solutes=solutes)


if __name__ == '__main__':
    print('=== 单气体 ===')
    for gas in ['ch4', 'co2', 'n2', 'o2', 'h2', 'he']:
        flu = create_gas_aqueous(gas, P=10e6, T=300)
        print(f'{gas:4s}  {flu.name:12s}  components: {[c.name for c in flu.components]}')

    print()
    print('=== 多气体 ===')
    flu = create_gas_aqueous(['ch4', 'co2'], P=10e6, T=300)
    print(f'{flu.name}: {[c.name for c in flu.components]}')
