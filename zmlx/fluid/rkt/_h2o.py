"""纯水物性：密度、比热（Reaktoro + Supcrt98 数据库）.

    h2o_density(P, T)       → kg/m³
    h2o_specific_heat(P, T) → J/(kg·K)

与 zmlx.fluid.cp 的 H₂O 完全一致（两者均基于 IAPWS-97）。
"""

from reaktoro import (
    AqueousPhase,
    ChemicalProps,
    ChemicalState,
    ChemicalSystem,
    SupcrtDatabase,
    speciate,
)

_DB = SupcrtDatabase("supcrt98")
_SYS = None


def _get_system():
    global _SYS
    if _SYS is None:
        solution = AqueousPhase(speciate("H O"))
        _SYS = ChemicalSystem(_DB, solution)
    return _SYS


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

    system = _get_system()
    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.setSpeciesAmount("H2O(aq)", 55.5, "mol")

    props = ChemicalProps(state)
    return props.phaseProps("AqueousPhase").density()


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

    system = _get_system()
    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.setSpeciesAmount("H2O(aq)", 55.5, "mol")

    props = ChemicalProps(state)
    return props.specificHeatCapacityConstP()


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt._plot import plot_contours
    gui.execute(lambda: plot_contours("H2O", h2o_density, h2o_specific_heat),
                close_after_done=False)
