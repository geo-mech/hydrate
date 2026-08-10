"""含溶解 N₂ 的水溶液密度（基于 Reaktoro + PHREEQC 数据库）."""

from reaktoro import (
    AqueousPhase,
    ChemicalProps,
    ChemicalState,
    ChemicalSystem,
    EquilibriumSolver,
    EquilibriumSpecs,
    GaseousPhase,
    PhreeqcDatabase,
    speciate,
)

_sys_cache = None
_solver_cache = None


def _get_system_and_solver():
    """获取缓存的 H₂O-N₂ 化学系统及平衡求解器."""
    global _sys_cache, _solver_cache
    if _sys_cache is None:
        db = PhreeqcDatabase("phreeqc.dat")
        solution = AqueousPhase(speciate("H O N"))
        gases = GaseousPhase(speciate("N"))
        _sys_cache = ChemicalSystem(db, solution, gases)
        specs = EquilibriumSpecs(_sys_cache)
        specs.temperature()
        specs.pressure()
        _solver_cache = EquilibriumSolver(specs)
    return _sys_cache, _solver_cache


def h2o_n2_density(w, P=10.0e6, T=300.0):
    """获取含溶解 N₂ 的水溶液密度.

    Args:
        w: N₂ 的质量分数，m(N₂) / (m(N₂) + m(H₂O))，范围 [0, 1)
        P: 压力 (Pa)，默认 10 MPa
        T: 温度 (K)，默认 300 K

    Returns:
        水溶液的密度 (kg/m³)
    """
    if not (0.0 <= w < 1.0):
        raise ValueError(f"w must be in [0, 1), got {w}")
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")

    m_h2o = 1.0
    if w <= 0:
        n_n2 = 0.0
    else:
        m_n2 = w / (1.0 - w) * m_h2o
        M_n2 = 0.028013  # kg/mol
        n_n2 = m_n2 / M_n2

    system, solver = _get_system_and_solver()

    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2O", m_h2o, "kg")
    state.set("N2", n_n2, "mol")

    solver.solve(state)

    props = ChemicalProps(state)
    return props.phaseProps("AqueousPhase").density()


M_N2 = 0.028013


def h2o_n2_solubility(P=10.0e6, T=300.0):
    """获取 N₂ 在水中的饱和溶解度（质量分数）.

    Args:
        P: 压力 (Pa)，默认 10 MPa
        T: 温度 (K)，默认 300 K

    Returns:
        饱和质量分数 w_sat
    """
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")

    system, solver = _get_system_and_solver()

    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2O", 1.0, "kg")
    state.set("N2", 0.1, "mol")  # 过量

    solver.solve(state)

    props = ChemicalProps(state)
    aq_mass = props.phaseProps("AqueousPhase").mass()
    return (aq_mass - 1.0) / aq_mass


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt.aq._plot import plot_density_ratio
    gui.execute(lambda: plot_density_ratio("N2", h2o_n2_density, w_max=0.003, color="navy",
                                            fn_solubility=h2o_n2_solubility),
                close_after_done=False)
