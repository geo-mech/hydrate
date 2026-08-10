"""纯水物性：密度、粘度、比热（CoolProp + IAPWS-97 状态方程）.

    h2o_density(P, T)       → kg/m³
    h2o_viscosity(P, T)     → Pa·s
    h2o_specific_heat(P, T) → J/(kg·K)

与 zmlx.fluid.rkt 的 H₂O 完全一致（两者均基于 IAPWS-97）。
"""

from CoolProp.CoolProp import PropsSI

_FLUID = "Water"


def h2o_density(P, T):
    """获取纯水在给定压力和温度下的密度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        水的密度 (kg/m³)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("D", "T", T, "P", P, _FLUID)


def h2o_viscosity(P, T):
    """获取纯水在给定压力和温度下的动力粘度.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        水的动力粘度 (Pa·s)
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("V", "T", T, "P", P, _FLUID)


def h2o_specific_heat(P, T):
    """获取纯水在给定压力和温度下的定压比热容.

    Args:
        P: 压力 (Pa)
        T: 温度 (K)

    Returns:
        水的定压比热容 (J/(kg·K))
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")
    return PropsSI("C", "T", T, "P", P, _FLUID)


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.cp._plot import plot_contours
    gui.execute(lambda: plot_contours("H2O", h2o_density, h2o_viscosity, h2o_specific_heat),
                close_after_done=False)
