"""氢气密度和比热（基于 Reaktoro + Supcrt98 数据库）."""

from reaktoro import (
    ChemicalProps,
    ChemicalState,
    ChemicalSystem,
    GaseousPhase,
    SupcrtDatabase,
    speciate,
)

_DB = SupcrtDatabase("supcrt98")
_SYS = None


def _get_system():
    global _SYS
    if _SYS is None:
        gases = GaseousPhase(speciate("H"))
        _SYS = ChemicalSystem(_DB, gases)
    return _SYS


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

    system = _get_system()
    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2(g)", 1.0, "mol")

    props = ChemicalProps(state)
    return props.phaseProps("GaseousPhase").density()


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

    system = _get_system()
    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2(g)", 1.0, "mol")

    props = ChemicalProps(state)
    return props.specificHeatCapacityConstP()


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt._plot import plot_contours
    gui.execute(lambda: plot_contours("H2", h2_density, h2_specific_heat),
                close_after_done=False)
