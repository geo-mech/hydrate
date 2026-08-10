"""氢气密度、粘度和比热（基于 CoolProp）."""

from CoolProp.CoolProp import PropsSI

_FLUID = "Hydrogen"


def h2_density(P, T):
    """获取氢气在给定压力和温度下的密度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氢气的密度 (kg/m³)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("D", "T", T, "P", P, _FLUID)


def h2_viscosity(P, T):
    """获取氢气在给定压力和温度下的动力粘度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氢气的动力粘度 (Pa·s)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("V", "T", T, "P", P, _FLUID)


def h2_specific_heat(P, T):
    """获取氢气在给定压力和温度下的定压比热容.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        氢气的定压比热容 (J/(kg·K))
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("C", "T", T, "P", P, _FLUID)


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.cp._plot import plot_contours
    gui.execute(lambda: plot_contours("H2", h2_density, h2_viscosity, h2_specific_heat),
                close_after_done=False)
