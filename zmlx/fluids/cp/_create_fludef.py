"""基于 CoolProp 自动创建 FluDef 插值表."""

import numpy as np

# 流体名 → CoolProp 名称
_FLUIDS = {
    'h2o': 'Water',
    'water': 'Water',
    'h2': 'Hydrogen',
    'hydrogen': 'Hydrogen',
    'he': 'Helium',
    'helium': 'Helium',
    'ch4': 'Methane',
    'methane': 'Methane',
    'c2h6': 'Ethane',
    'ethane': 'Ethane',
    'n2': 'Nitrogen',
    'nitrogen': 'Nitrogen',
    'o2': 'Oxygen',
    'oxygen': 'Oxygen',
    'co2': 'CO2',
}


def create_fludef(fluid, t_min=280.0, t_max=500.0, p_min=1e5, p_max=30e6,
                  name=None):
    """基于 CoolProp 创建 FluDef.

    在压力/温度范围内采样密度和粘度，生成 Interp2 插值表。
    比热取范围内若干采样点的平均值。

    Args:
        fluid: 流体名称，如 'h2o' / 'water', 'ch4' / 'methane'
        t_min: 最低温度 (K)
        t_max: 最高温度 (K)
        p_min: 最低压力 (Pa)
        p_max: 最高压力 (Pa)
        name: FluDef 名称（默认使用 fluid）

    Returns:
        FluDef
    """
    from CoolProp.CoolProp import PropsSI
    from zmlx.exts import FluDef, Interp2

    fluid = fluid.lower()
    if fluid not in _FLUIDS:
        raise ValueError(f"Unknown fluid '{fluid}'. Valid: {list(_FLUIDS.keys())}")
    cp_name = _FLUIDS[fluid]

    if name is None:
        name = fluid

    # 采样密度/粘度到 Interp2（步长与 ch4.py 一致）
    def _make_interp(fn):
        interp = Interp2()
        interp.create(p_min, 0.1e6, p_max, t_min, 1.0, t_max, fn)
        return interp

    def _get_density(P, T):
        return PropsSI("D", "T", T, "P", P, cp_name)

    def _get_viscosity(P, T):
        return PropsSI("V", "T", T, "P", P, cp_name)

    # 比热均值
    Ts = np.linspace(t_min, t_max, 7)
    Ps = np.linspace(p_min, p_max, 7)
    cp_vals = []
    for T in Ts:
        for P in Ps:
            try:
                cp_vals.append(PropsSI("C", "T", T, "P", P, cp_name))
            except Exception:
                pass
    specific_heat = float(np.mean(cp_vals)) if cp_vals else 4200.0

    return FluDef(
        den=_make_interp(_get_density),
        vis=_make_interp(_get_viscosity),
        specific_heat=specific_heat,
        name=name,
    )


if __name__ == '__main__':
    from zmlx.ui import gui
    from zmlx.plt import show_flu_def

    def show():
        flu = create_fludef('ch4', name='ch4_cp')
        show_flu_def(flu, [4e6, 15e6], [274, 290])

    gui.execute(show, close_after_done=False)
