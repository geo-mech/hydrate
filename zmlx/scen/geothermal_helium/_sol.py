from typing import Callable, Union, Optional
from math import exp
from zmlx.tfc import flu_keys, Seepage, cell_keys
from zmlx.react import melt

# ==========================================
# IAPWS 官方热力学基准常数
# ==========================================
T_C1 = 647.096  # 纯水临界温度 (K)
P_C1 = 22.064e6  # 纯水临界压力 (Pa)


def calc_p1_star(T_kelvin):
    """
    使用 Wagner & Pruss 关联式计算纯水在温度 T(K) 下的饱和蒸汽压 (Pa)。
    """
    Tr = T_kelvin / T_C1
    tau = 1.0 - Tr

    a = [-7.85951783, 1.84408259, -11.7866497, 22.6807411, -15.9618719, 1.80122502]
    b = [1.0, 1.5, 3.0, 3.5, 4.0, 7.5]

    sum_term = sum(a[i] * (tau ** b[i]) for i in range(6))
    ln_pratio = sum_term / Tr
    p1_star = P_C1 * exp(ln_pratio)
    return p1_star


def get_henry_constant(T_kelvin, gas_type='He'):
    """
    计算特定气体在水中的亨利常数 (Pa)。
    """
    Tr = T_kelvin / T_C1
    tau = 1.0 - Tr
    p1_star = calc_p1_star(T_kelvin)

    if gas_type == 'He':
        A, B, C_param = -3.52839, 7.12983, 4.47770
    elif gas_type == 'N2':
        A, B, C_param = -9.67578, 4.72162, 11.70585
    else:
        raise ValueError(f"暂未收录该气体 '{gas_type}' 的参数，请查阅 IAPWS 文献扩充。")

    term1 = A / Tr
    term2 = B * (tau ** 0.355) / Tr
    term3 = C_param * (Tr ** -0.41) * exp(tau)

    ln_kh_ratio = term1 + term2 + term3
    k_H = p1_star * exp(ln_kh_ratio)
    return k_H


def get_he_sol(pressure, temperature):
    """
    计算给定压力(Pa)和温度(K)下氦气的溶解度 (质量分数极限)
    """
    k_H = get_henry_constant(temperature, 'He')

    # 1. 计算摩尔分数: x = P / k_H
    mole_fraction = pressure / k_H

    # 2. 转化为质量分数: w = x * (M_gas / M_H2O)
    # He 摩尔质量约 0.004 kg/mol，水约 0.018 kg/mol
    mass_fraction = mole_fraction * (0.004 / 0.018)

    # 保证返回值在物理和框架允许的安全区间内 [0, 0.1]
    return max(0.0, min(mass_fraction, 0.1))


def get_n2_sol(pressure, temperature):
    """
    计算给定压力(Pa)和温度(K)下氮气的溶解度 (质量分数极限)
    """
    k_H = get_henry_constant(temperature, 'N2')

    # N2 摩尔质量约 0.028 kg/mol
    mole_fraction = pressure / k_H
    mass_fraction = mole_fraction * (0.028 / 0.018)

    return max(0.0, min(mass_fraction, 0.1))


def update_solubility(model: Seepage, ca: int, sol: Union[Callable, float]):
    """
    更新溶解度属性(根据压力和温度计算)
    Args:
    model: 计算模型
    ca: 溶解度属性的索引
    sol: 获取溶解度的函数 get_sol(pressure, temperature) -> solubility
    Returns:
    None
    """
    fid = model.find_fludef('liq')
    assert fid is not None
    assert len(fid) > 0

    fa_t = flu_keys(model).temperature
    for cell in model.cells:
        if callable(sol):
            liq = cell.get_fluid(*fid)
            assert liq is not None
            temp = liq.get_attr(index=fa_t)
            pressure = cell.pre
            v = sol(pressure, temp)
            assert 0.0 <= v <= 0.1
            cell.set_attr(ca, v)
        else:
            cell.set_attr(ca, sol)


def update_he_sol(model: Seepage, sol: Optional[Union[float, Callable]] = None):
    if sol is None:
        sol = get_he_sol
    ca = cell_keys(model)
    update_solubility(model, ca=ca.he_sol, sol=sol)


def update_n2_sol(model: Seepage, sol: Optional[Union[float, Callable]] = None):
    if sol is None:
        sol = get_n2_sol
    ca = cell_keys(model)
    update_solubility(model, ca=ca.n2_sol, sol=sol)
