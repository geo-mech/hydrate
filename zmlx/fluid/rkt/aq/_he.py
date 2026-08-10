"""含溶解 He 的水溶液密度（基于 Reaktoro + LLNL 数据库）.

注意：PHREEQC 标准数据库不含 He，需使用 LLNL 数据库。
"""

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
    """获取缓存的 H₂O-He 化学系统及平衡求解器（LLNL 数据库）."""
    global _sys_cache, _solver_cache
    if _sys_cache is None:
        db = PhreeqcDatabase("llnl.dat")
        solution = AqueousPhase(speciate("H O He"))
        gases = GaseousPhase(speciate("He"))
        _sys_cache = ChemicalSystem(db, solution, gases)
        specs = EquilibriumSpecs(_sys_cache)
        specs.temperature()
        specs.pressure()
        _solver_cache = EquilibriumSolver(specs)
    return _sys_cache, _solver_cache


def h2o_he_density(w, P=10.0e6, T=300.0):
    """获取含溶解 He 的水溶液密度.

    He 化学惰性，溶解度极低。

    Args:
        w: He 的质量分数，m(He) / (m(He) + m(H₂O))，范围 [0, 1)
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
        n_he = 0.0
    else:
        m_he = w / (1.0 - w) * m_h2o
        M_he = 0.0040026  # kg/mol
        n_he = m_he / M_he

    system, solver = _get_system_and_solver()

    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2O", m_h2o, "kg")
    state.set("He", n_he, "mol")

    solver.solve(state)

    props = ChemicalProps(state)
    return props.phaseProps("AqueousPhase").density()


def h2o_he_solubility(P=10.0e6, T=300.0):
    """获取 He 在水中的饱和溶解度（质量分数）.

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
    state.set("He", 0.1, "mol")  # 过量

    solver.solve(state)

    props = ChemicalProps(state)
    aq_mass = props.phaseProps("AqueousPhase").mass()
    return (aq_mass - 1.0) / aq_mass


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt.aq._plot import plot_density_ratio
    gui.execute(lambda: plot_density_ratio("He", h2o_he_density, w_max=0.0002, color="goldenrod",
                                            fn_solubility=h2o_he_solubility),
                close_after_done=False)
