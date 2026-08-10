"""氦气物性：密度、粘度、比热（CoolProp）.

    he_density(P, T)       → kg/m³
    he_viscosity(P, T)     → Pa·s
    he_specific_heat(P, T) → J/(kg·K)

与 zmlx.fluid.rkt 的 He 高度一致（误差 < 1%），单原子气体 EOS 简单。
"""

from CoolProp.CoolProp import PropsSI

_FLUID = "Helium"


def he_density(P, T):
    """获取氦气在给定压力和温度下的密度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氦气的密度 (kg/m³)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("D", "T", T, "P", P, _FLUID)


def he_viscosity(P, T):
    """获取氦气在给定压力和温度下的动力粘度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氦气的动力粘度 (Pa·s)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("V", "T", T, "P", P, _FLUID)


def he_specific_heat(P, T):
    """获取氦气在给定压力和温度下的定压比热容.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氦气的定压比热容 (J/(kg·K))
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("C", "T", T, "P", P, _FLUID)


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.cp._plot import plot_contours
    gui.execute(lambda: plot_contours("He", he_density, he_viscosity, he_specific_heat),
                close_after_done=False)
