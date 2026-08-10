"""含溶解 CH₄ 的水溶液密度（Reaktoro + PHREEQC 数据库）.

    h2o_ch4_density(w, P=10e6, T=300) → kg/m³

CH₄ 在 300K/10MPa 下饱和溶解度约 w ≈ 0.0025 (0.25%)。
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

# 缓存的系统和求解器
_sys_cache = None
_solver_cache = None


def _get_system_and_solver():
    """获取缓存的 H₂O-CH₄ 化学系统及平衡求解器."""
    global _sys_cache, _solver_cache
    if _sys_cache is None:
        db = PhreeqcDatabase("phreeqc.dat")
        solution = AqueousPhase(speciate("H O C"))
        gases = GaseousPhase(speciate("C H"))
        _sys_cache = ChemicalSystem(db, solution, gases)
        specs = EquilibriumSpecs(_sys_cache)
        specs.temperature()
        specs.pressure()
        _solver_cache = EquilibriumSolver(specs)
    return _sys_cache, _solver_cache


def h2o_ch4_density(w, P=10.0e6, T=300.0):
    """获取含溶解甲烷的水溶液密度.

    CH₄ 在气-液两相间按热力学平衡分配：
    - 低于饱和溶解度时全部溶解
    - 超过饱和时水相为 CH₄ 饱和态，多余进入气相

    Args:
        w: CH₄ 的质量分数，m(CH₄) / (m(CH₄) + m(H₂O))，范围 [0, 1)
        P: 压力 (Pa)，默认 10 MPa
        T: 温度 (K)，默认 300 K

    Returns:
        水溶液的密度 (kg/m³)

    Examples:
        >>> h2o_ch4_density(0.0)               # 纯水，300K, 10MPa
        >>> h2o_ch4_density(0.01, P=5e6)       # 1% CH₄, 300K, 5MPa
        >>> h2o_ch4_density(0.01, T=350)        # 1% CH₄, 350K, 10MPa
    """
    if not (0.0 <= w < 1.0):
        raise ValueError(f"w must be in [0, 1), got {w}")
    if P <= 0:
        raise ValueError(f"P must be > 0, got {P}")
    if T <= 0:
        raise ValueError(f"T must be > 0, got {T}")

    # 以 1 kg H₂O 为基准
    m_h2o = 1.0  # kg
    if w <= 0:
        n_ch4 = 0.0
    else:
        m_ch4 = w / (1.0 - w) * m_h2o  # kg
        M_ch4 = 0.016043  # kg/mol
        n_ch4 = m_ch4 / M_ch4  # mol

    system, solver = _get_system_and_solver()

    state = ChemicalState(system)
    state.temperature(T, "K")
    state.pressure(P, "Pa")
    state.set("H2O", m_h2o, "kg")
    if n_ch4 > 0:
        state.set("CH4", n_ch4, "mol")

    # 平衡计算：自动分配 CH₄ 到水相和气相
    solver.solve(state)

    props = ChemicalProps(state)
    return props.phaseProps("AqueousPhase").density()


M_CH4 = 0.016043  # kg/mol


def h2o_ch4_solubility(P=10.0e6, T=300.0):
    """获取 CH₄ 在水中的饱和溶解度（质量分数）.

    过量 CH₄ 平衡后，通过水相质量推算溶解量。

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
    state.set("CH4", 1.0, "mol")  # 过量

    solver.solve(state)

    props = ChemicalProps(state)
    aq_mass = props.phaseProps("AqueousPhase").mass()
    return (aq_mass - 1.0) / aq_mass


if __name__ == "__main__":
    from zmlx.ui import gui
    from zmlx.fluid.rkt.aq._plot import plot_density_ratio
    gui.execute(lambda: plot_density_ratio("CH4", h2o_ch4_density, w_max=0.003,
                                            fn_solubility=h2o_ch4_solubility),
                close_after_done=False)
