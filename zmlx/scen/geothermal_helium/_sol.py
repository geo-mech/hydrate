# -*- coding: utf-8 -*-

from typing import Callable, Union, Optional, Dict, Any
from math import exp
import warnings

import numpy as np

from zmlx.tfc import flu_keys, Seepage, cell_keys
from zmlx.tfc._base import as_numpy


"""
Henry 溶解度 + He/N2/CH4 多组分泡点判据模块

用途：
1. 计算 He、N2、CH4 在水中的 Henry 常数；
2. 计算给定 P-T 条件下的单组分溶解度上限；
3. 更新 zmlx cell 属性中的 he_sol、n2_sol、ch4_sol 溶解度上限；
4. 根据当前网格中的实际 He/N2/CH4 质量分数，计算多组分泡点压力；
5. 给出 P_bubble / P_cell 作为脱溶风险判据。

重要说明：
当前模块只负责“判据”和“溶解度上限”。
它不会自动把 he_sol、n2_sol、ch4_sol 转移到气相。
真正的质量转移需要后续再接 melt 或自定义质量转移函数。
"""


# ============================================================
# 1. IAPWS 基准常数
# ============================================================

T_C1 = 647.096        # 纯水临界温度，K
P_C1 = 22.064e6       # 纯水临界压力，Pa

M_WATER = 18.015268e-3     # kg/mol

MOLAR_MASS = {
    "He": 4.0026e-3,
    "N2": 28.0134e-3,
    "CH4": 16.043e-3,
}

# IAPWS Henry 公式适用温度范围，K
# 超出时仍可计算，但会给出 warning
HENRY_T_LIMIT = {
    "He": (273.21, 553.18),
    "N2": (278.12, 636.46),
    "CH4": (275.46, 633.11),
}

# IAPWS Henry 参数：A, B, C
HENRY_ABC = {
    "He": (-3.52839, 7.12983, 4.47770),
    "N2": (-9.67578, 4.72162, 11.70585),
    "CH4": (-10.44708, 4.66491, 12.12986),
}

GAS_TO_FLUID_NAME = {
    "He": "he_sol",
    "N2": "n2_sol",
    "CH4": "ch4_sol",
}

FLUID_NAME_TO_GAS = {
    "he_sol": "He",
    "n2_sol": "N2",
    "ch4_sol": "CH4",
}


# ============================================================
# 2. 基础工具
# ============================================================

def normalize_gas_name(gas_type: str) -> str:
    """
    统一气体名称。
    支持：
        He, he, he_sol
        N2, n2, n2_sol
        CH4, ch4, ch4_sol
    """
    s = str(gas_type).strip()

    if s in ("He", "HE", "he", "he_sol", "He_sol"):
        return "He"

    if s in ("N2", "n2", "N2_sol", "n2_sol"):
        return "N2"

    if s in ("CH4", "ch4", "Ch4", "ch4_sol", "CH4_sol"):
        return "CH4"

    raise ValueError(f"未知气体类型: {gas_type}")


def safe_divide(a, b, default=0.0):
    if abs(b) <= 0.0:
        return default
    return a / b


# ============================================================
# 3. IAPWS 饱和蒸汽压
# ============================================================

def calc_p1_star(T_kelvin: float) -> float:
    """
    使用 Wagner & Pruss 形式计算纯水在温度 T(K) 下的饱和蒸汽压。

    返回：
        p1_star, Pa
    """
    Tr = T_kelvin / T_C1
    tau = 1.0 - Tr

    a = [
        -7.85951783,
        1.84408259,
        -11.7866497,
        22.6807411,
        -15.9618719,
        1.80122502,
    ]

    b = [1.0, 1.5, 3.0, 3.5, 4.0, 7.5]

    sum_term = sum(a[i] * (tau ** b[i]) for i in range(6))
    ln_pratio = sum_term / Tr

    p1_star = P_C1 * exp(ln_pratio)
    return p1_star


# ============================================================
# 4. Henry 常数
# ============================================================

def get_henry_constant(T_kelvin: float, gas_type: str = "He") -> float:
    """
    计算 Henry 常数 k_H。

    使用形式：
        p_i = k_H * x_i

    其中：
        p_i 为气体分压，Pa；
        x_i 为水相中气体摩尔分数；
        k_H 单位 Pa。

    注意：
        这是 IAPWS Henry constant 形式，不是 Hcp = C / p 的形式。
    """
    gas = normalize_gas_name(gas_type)

    Tmin, Tmax = HENRY_T_LIMIT[gas]
    if T_kelvin < Tmin or T_kelvin > Tmax:
        warnings.warn(
            f"{gas} Henry 参数温度范围为 {Tmin:.2f}-{Tmax:.2f} K，"
            f"当前 T={T_kelvin:.2f} K，结果属于外推。"
        )

    Tr = T_kelvin / T_C1
    tau = 1.0 - Tr
    p1_star = calc_p1_star(T_kelvin)

    A, B, C_param = HENRY_ABC[gas]

    ln_kh_ratio = (
        A / Tr
        + B * (tau ** 0.355) / Tr
        + C_param * (Tr ** -0.41) * exp(tau)
    )

    k_H = p1_star * exp(ln_kh_ratio)

    return k_H


# ============================================================
# 5. 摩尔分数与质量分数换算
# ============================================================

def mole_fraction_to_mass_fraction(
        x_gas: float,
        gas_type: str,
        max_value: Optional[float] = None
) -> float:
    """
    将水相中某气体摩尔分数 x_gas 转为二元水-气体系下的质量分数。

    对稀溶液，和 x * M_gas / M_water 的近似结果接近；
    但这个函数更稳。
    """
    gas = normalize_gas_name(gas_type)
    M_gas = MOLAR_MASS[gas]

    x = max(0.0, min(float(x_gas), 0.999999999))

    w = (x * M_gas) / (x * M_gas + (1.0 - x) * M_WATER)

    if max_value is not None:
        w = max(0.0, min(w, max_value))

    return w


def mass_fractions_to_liquid_mole_fractions(
        w_h2o: float,
        w_he: float,
        w_n2: float,
        w_ch4: float
) -> Dict[str, float]:
    """
    将 h2o、he_sol、n2_sol、ch4_sol 的质量份额换算为水相摩尔分数。

    输入质量份额不要求严格加和为 1；
    函数内部按摩尔数计算。
    """
    w_h2o = max(float(w_h2o), 0.0)
    w_he = max(float(w_he), 0.0)
    w_n2 = max(float(w_n2), 0.0)
    w_ch4 = max(float(w_ch4), 0.0)

    n_h2o = w_h2o / M_WATER if M_WATER > 0.0 else 0.0
    n_he = w_he / MOLAR_MASS["He"]
    n_n2 = w_n2 / MOLAR_MASS["N2"]
    n_ch4 = w_ch4 / MOLAR_MASS["CH4"]

    n_total = n_h2o + n_he + n_n2 + n_ch4

    if n_total <= 0.0:
        return {
            "H2O": 0.0,
            "He": 0.0,
            "N2": 0.0,
            "CH4": 0.0,
        }

    return {
        "H2O": n_h2o / n_total,
        "He": n_he / n_total,
        "N2": n_n2 / n_total,
        "CH4": n_ch4 / n_total,
    }


# ============================================================
# 6. 单组分溶解度上限
# ============================================================

def get_gas_solubility_mass_fraction(
        pressure: float,
        temperature: float,
        gas_type: str,
        gas_phase_mole_fraction: float = 1.0,
        max_value: float = 0.1
) -> float:
    """
    计算给定压力和温度下，某气体在水中的质量分数上限。

    参数：
        pressure:
            总压力，Pa。

        gas_phase_mole_fraction:
            气相中该气体摩尔分数 y_i。
            若为纯气体，取 1；
            若为混合气，应取 y_i。

    Henry 关系：
        p_i = y_i * P
        x_i = p_i / k_H

    返回：
        质量分数上限。
    """
    gas = normalize_gas_name(gas_type)

    y = max(0.0, min(float(gas_phase_mole_fraction), 1.0))
    p_i = max(float(pressure), 0.0) * y

    k_H = get_henry_constant(temperature, gas)

    if k_H <= 0.0:
        return 0.0

    x_i = p_i / k_H
    return mole_fraction_to_mass_fraction(x_i, gas, max_value=max_value)


def get_he_sol(pressure, temperature):
    """
    纯 He 条件下 He(aq) 质量分数上限。
    注意：这是 p_He = P 的单组分上限。
    """
    return get_gas_solubility_mass_fraction(
        pressure=pressure,
        temperature=temperature,
        gas_type="He",
        gas_phase_mole_fraction=1.0,
        max_value=0.1,
    )


def get_n2_sol(pressure, temperature):
    """
    纯 N2 条件下 N2(aq) 质量分数上限。
    注意：这是 p_N2 = P 的单组分上限。
    """
    return get_gas_solubility_mass_fraction(
        pressure=pressure,
        temperature=temperature,
        gas_type="N2",
        gas_phase_mole_fraction=1.0,
        max_value=0.1,
    )


def get_ch4_sol(pressure, temperature):
    """
    纯 CH4 条件下 CH4(aq) 质量分数上限。
    注意：这是 p_CH4 = P 的单组分上限。
    """
    return get_gas_solubility_mass_fraction(
        pressure=pressure,
        temperature=temperature,
        gas_type="CH4",
        gas_phase_mole_fraction=1.0,
        max_value=0.1,
    )


# ============================================================
# 7. zmlx cell 属性更新
# ============================================================

def update_solubility(model: Seepage, ca: int, sol: Union[Callable, float]):
    """
    更新某个 cell 属性中的溶解度上限。

    参数：
        ca:
            cell 属性索引，例如 cell_keys(model).he_sol。

        sol:
            可以是常数，也可以是函数：
                sol(pressure, temperature) -> mass_fraction_limit
    """
    fid = model.find_fludef("liq")
    if fid is None or len(fid) == 0:
        raise RuntimeError("没有找到流体定义 'liq'，请检查 fluid/create 定义。")

    fa_t = flu_keys(model).temperature

    for cell in model.cells:
        if callable(sol):
            liq = cell.get_fluid(*fid)
            if liq is None:
                continue

            temp = liq.get_attr(index=fa_t)
            pressure = cell.pre

            v = sol(pressure, temp)
            v = max(0.0, min(float(v), 0.1))

            cell.set_attr(ca, v)
        else:
            v = max(0.0, min(float(sol), 0.1))
            cell.set_attr(ca, v)


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


def update_ch4_sol(model: Seepage, sol: Optional[Union[float, Callable]] = None):
    if sol is None:
        sol = get_ch4_sol

    ca = cell_keys(model)
    update_solubility(model, ca=ca.ch4_sol, sol=sol)


def update_all_solubility(model: Seepage):
    """
    一次性更新 He、N2、CH4 的单组分溶解度上限。

    注意：
        这里写入的是“纯气体分压 = 当前压力”条件下的上限。
        多组分是否脱溶，应进一步看 calc_bubble_pressure_from_mass_fractions。
    """
    update_he_sol(model)
    update_n2_sol(model)
    update_ch4_sol(model)


# ============================================================
# 8. 多组分泡点压力判据
# ============================================================

def calc_bubble_pressure_from_mass_fractions(
        w_h2o: float,
        w_he: float,
        w_n2: float,
        w_ch4: float,
        temperature: float
) -> Dict[str, Any]:
    """
    根据当前水相中 He/N2/CH4 实际质量份额，计算混合气泡点压力。

    Henry 关系：
        p_i = k_H_i(T) * x_i

    多组分泡点：
        P_bubble = p_He + p_N2 + p_CH4

    判据：
        P_cell > P_bubble：未饱和，不脱溶
        P_cell = P_bubble：达到泡点
        P_cell < P_bubble：过饱和，有脱溶风险

    返回：
        dict，包括泡点压力、所需分压和泡点气相组成。
    """
    x = mass_fractions_to_liquid_mole_fractions(
        w_h2o=w_h2o,
        w_he=w_he,
        w_n2=w_n2,
        w_ch4=w_ch4,
    )

    p_req = {}
    P_bubble = 0.0

    for gas in ("He", "N2", "CH4"):
        k_H = get_henry_constant(temperature, gas)
        p_i = k_H * x[gas]
        p_req[gas] = p_i
        P_bubble += p_i

    if P_bubble > 0.0:
        y_bubble = {
            gas: p_req[gas] / P_bubble
            for gas in ("He", "N2", "CH4")
        }
    else:
        y_bubble = {
            "He": 0.0,
            "N2": 0.0,
            "CH4": 0.0,
        }

    return {
        "P_bubble": P_bubble,
        "p_req": p_req,
        "x_liquid": x,
        "y_bubble": y_bubble,
    }


def calc_saturation_index(
        pressure: float,
        temperature: float,
        w_h2o: float,
        w_he: float,
        w_n2: float,
        w_ch4: float
) -> Dict[str, Any]:
    """
    计算多组分饱和指数：

        SI = P_bubble / P_cell

    SI < 1：未饱和
    SI = 1：达到泡点
    SI > 1：有脱溶风险
    """
    r = calc_bubble_pressure_from_mass_fractions(
        w_h2o=w_h2o,
        w_he=w_he,
        w_n2=w_n2,
        w_ch4=w_ch4,
        temperature=temperature,
    )

    P_bubble = r["P_bubble"]
    P_cell = max(float(pressure), 1.0)

    si = P_bubble / P_cell

    r["pressure"] = P_cell
    r["saturation_index"] = si
    r["exsolve_risk"] = si > 1.0

    return r


# ============================================================
# 9. 从 zmlx 模型计算逐网格脱溶诊断数组
# ============================================================

def _get_cell_temperature_array(model: Seepage) -> np.ndarray:
    """
    从 liq 相读取每个 cell 的温度。
    """
    fid = model.find_fludef("liq")
    if fid is None or len(fid) == 0:
        raise RuntimeError("没有找到流体定义 'liq'，请检查 fluid/create 定义。")

    fa_t = flu_keys(model).temperature

    n = len(model.cells)
    temps = np.zeros(n, dtype=float)

    for cell in model.cells:
        liq = cell.get_fluid(*fid)
        if liq is None:
            temps[cell.index] = np.nan
        else:
            temps[cell.index] = liq.get_attr(index=fa_t)

    return temps


def compute_exsolution_diagnostics(model: Seepage) -> Dict[str, np.ndarray]:
    """
    计算整个模型每个网格的脱溶风险诊断。

    返回数组包括：
        pressure
        temperature
        w_h2o, w_he, w_n2, w_ch4
        P_bubble
        saturation_index = P_bubble / P_cell
        exsolve_risk
        x_he, x_n2, x_ch4
        y_he_bubble, y_n2_bubble, y_ch4_bubble
        he_single_ratio, n2_single_ratio, ch4_single_ratio

    其中：
        saturation_index > 1 表示该网格有多组分脱溶风险。
    """
    np_model = as_numpy(model)

    cells = np_model.cells

    pressure = np.array([cell.pre for cell in model.cells], dtype=float)
    temperature = _get_cell_temperature_array(model)

    total_mass = cells.fluid_mass

    h2o_mass = as_numpy(model).fluids("h2o").mass
    he_mass = as_numpy(model).fluids("he_sol").mass
    n2_mass = as_numpy(model).fluids("n2_sol").mass
    ch4_mass = as_numpy(model).fluids("ch4_sol").mass

    valid = total_mass > 0.0

    w_h2o = np.zeros_like(total_mass, dtype=float)
    w_he = np.zeros_like(total_mass, dtype=float)
    w_n2 = np.zeros_like(total_mass, dtype=float)
    w_ch4 = np.zeros_like(total_mass, dtype=float)

    w_h2o[valid] = h2o_mass[valid] / total_mass[valid]
    w_he[valid] = he_mass[valid] / total_mass[valid]
    w_n2[valid] = n2_mass[valid] / total_mass[valid]
    w_ch4[valid] = ch4_mass[valid] / total_mass[valid]

    n = len(total_mass)

    P_bubble = np.zeros(n, dtype=float)
    saturation_index = np.zeros(n, dtype=float)

    x_he = np.zeros(n, dtype=float)
    x_n2 = np.zeros(n, dtype=float)
    x_ch4 = np.zeros(n, dtype=float)

    y_he_bubble = np.zeros(n, dtype=float)
    y_n2_bubble = np.zeros(n, dtype=float)
    y_ch4_bubble = np.zeros(n, dtype=float)

    he_single_ratio = np.zeros(n, dtype=float)
    n2_single_ratio = np.zeros(n, dtype=float)
    ch4_single_ratio = np.zeros(n, dtype=float)

    for i in range(n):
        if not valid[i]:
            continue

        T = temperature[i]
        P = pressure[i]

        if not np.isfinite(T) or T <= 0.0 or P <= 0.0:
            continue

        r = calc_saturation_index(
            pressure=P,
            temperature=T,
            w_h2o=w_h2o[i],
            w_he=w_he[i],
            w_n2=w_n2[i],
            w_ch4=w_ch4[i],
        )

        P_bubble[i] = r["P_bubble"]
        saturation_index[i] = r["saturation_index"]

        x_he[i] = r["x_liquid"]["He"]
        x_n2[i] = r["x_liquid"]["N2"]
        x_ch4[i] = r["x_liquid"]["CH4"]

        y_he_bubble[i] = r["y_bubble"]["He"]
        y_n2_bubble[i] = r["y_bubble"]["N2"]
        y_ch4_bubble[i] = r["y_bubble"]["CH4"]

        # 单组分实际含量 / 纯气体上限，仅作为辅助参考
        he_lim = get_he_sol(P, T)
        n2_lim = get_n2_sol(P, T)
        ch4_lim = get_ch4_sol(P, T)

        he_single_ratio[i] = safe_divide(w_he[i], he_lim, default=0.0)
        n2_single_ratio[i] = safe_divide(w_n2[i], n2_lim, default=0.0)
        ch4_single_ratio[i] = safe_divide(w_ch4[i], ch4_lim, default=0.0)

    exsolve_risk = saturation_index > 1.0

    return {
        "pressure": pressure,
        "temperature": temperature,

        "w_h2o": w_h2o,
        "w_he": w_he,
        "w_n2": w_n2,
        "w_ch4": w_ch4,

        "P_bubble": P_bubble,
        "P_bubble_MPa": P_bubble / 1.0e6,
        "saturation_index": saturation_index,
        "exsolve_risk": exsolve_risk,

        "x_he": x_he,
        "x_n2": x_n2,
        "x_ch4": x_ch4,

        "y_he_bubble": y_he_bubble,
        "y_n2_bubble": y_n2_bubble,
        "y_ch4_bubble": y_ch4_bubble,

        "he_single_ratio": he_single_ratio,
        "n2_single_ratio": n2_single_ratio,
        "ch4_single_ratio": ch4_single_ratio,
    }


# ============================================================
# 10. 简单打印摘要
# ============================================================

def print_exsolution_summary(model: Seepage, title: str = "Exsolution diagnostic"):
    """
    打印当前模型的脱溶风险摘要。
    """
    d = compute_exsolution_diagnostics(model)

    si = d["saturation_index"]
    pb = d["P_bubble_MPa"]
    risk = d["exsolve_risk"]

    valid = np.isfinite(si)

    if not np.any(valid):
        print(f"\n========== {title} ==========")
        print("没有有效网格。")
        print("================================\n")
        return

    print(f"\n========== {title} ==========")
    print(f"有效网格数 = {int(np.sum(valid))}")
    print(f"脱溶风险网格数 = {int(np.sum(risk & valid))}")
    print(f"P_bubble 最大值 = {np.nanmax(pb[valid]):.6e} MPa")
    print(f"P_bubble 平均值 = {np.nanmean(pb[valid]):.6e} MPa")
    print(f"P_bubble / P 最大值 = {np.nanmax(si[valid]):.6e}")
    print(f"P_bubble / P 平均值 = {np.nanmean(si[valid]):.6e}")

    if np.nanmax(si[valid]) > 1.0:
        print("判断：模型中存在 P_bubble / P > 1 的网格，有脱溶风险。")
    else:
        print("判断：当前模型中 P_bubble / P <= 1，暂未达到脱溶条件。")

    print("================================\n")