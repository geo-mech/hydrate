"""含溶解 O₂ 的水溶液密度（基于 Reaktoro + PHREEQC 数据库）."""

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
    """获取缓存的 H₂O-O₂ 化学系统及平衡求解器."""
    global _sys_cache, _solver_cache
    if _sys_cache is None:
        db = PhreeqcDatabase("phreeqc.dat")
        solution = AqueousPhase(speciate("H O"))
        gases = GaseousPhase(speciate("O"))
        _sys_cache = ChemicalSystem(db, solution, gases)
        specs = EquilibriumSpecs(_sys_cache)
        specs.temperature()
        specs.pressure()
        _solver_cache = EquilibriumSolver(specs)
    return _sys_cache, _solver_cache


def h2o_o2_density(w, P=10.0e6, T=300.0):
    """获取含溶解 O₂ 的水溶液密度.

    Args:
        w: O₂ 的质量分数，m(O₂) / (m(O₂) + m(H₂O))，范围 [0, 1)
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
        n_o2 = 0.0
    else:
        m_o2 = w / (1.0 - w) * m_h2o
        M_o2 = 0.031998  # kg/mol
        n_o2 = m_o2 / M_o2

    system, solver = _get_system_and_solver()

    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2O", m_h2o, "kg")
    state.set("O2", n_o2, "mol")

    solver.solve(state)

    props = ChemicalProps(state)
    return props.phaseProps("AqueousPhase").density()


def h2o_o2_solubility(P=10.0e6, T=300.0):
    """获取 O₂ 在水中的饱和溶解度（质量分数）.

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
    state.set("O2", 0.1, "mol")  # 过量

    solver.solve(state)

    props = ChemicalProps(state)
    aq_mass = props.phaseProps("AqueousPhase").mass()
    return (aq_mass - 1.0) / aq_mass


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt.aq._plot import plot_density_ratio
    gui.execute(lambda: plot_density_ratio("O2", h2o_o2_density, w_max=0.01, color="crimson",
                                            fn_solubility=h2o_o2_solubility),
                close_after_done=False)
