"""二氧化碳物性：密度、粘度、比热（CoolProp + Helmholtz EOS）.

    co2_density(P, T)       → kg/m³
    co2_viscosity(P, T)     → Pa·s
    co2_specific_heat(P, T) → J/(kg·K)

注意：CO₂ 临界点 Tc=304.1K, Pc=7.38MPa。在近临界区 CoolProp 与
Reaktoro (Supcrt98) 差异显著，工程计算推荐使用本模块。
"""

from CoolProp.CoolProp import PropsSI

_FLUID = "CO2"


def co2_density(P, T):
    """获取二氧化碳在给定压力和温度下的密度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        二氧化碳的密度 (kg/m³)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("D", "T", T, "P", P, _FLUID)


def co2_viscosity(P, T):
    """获取二氧化碳在给定压力和温度下的动力粘度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        二氧化碳的动力粘度 (Pa·s)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("V", "T", T, "P", P, _FLUID)


def co2_specific_heat(P, T):
    """获取二氧化碳在给定压力和温度下的定压比热容.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        二氧化碳的定压比热容 (J/(kg·K))
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("C", "T", T, "P", P, _FLUID)


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.cp._plot import plot_contours
    gui.execute(lambda: plot_contours("CO2", co2_density, co2_viscosity, co2_specific_heat),
                close_after_done=False)
