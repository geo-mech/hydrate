"""
Define the property of oil.

data From Maryelin. 2022.11.16

by 张召彬

注意，此处定义的oil为重油，粘度非常大，如下所示，可见在温度低于350K的时候，它的粘性比水大了
将近3个数量级，因此几乎是很难流动的。

这个油必须加热，才能具有有效的流动性

p = 10000000.0Pa, T = 280K, vis = 5251.493255037484Pa.s, den = 1021.593999kg/m^3
p = 10000000.0Pa, T = 300K, vis = 177.86679222419696Pa.s, den = 1010.364799kg/m^3
p = 10000000.0Pa, T = 350K, vis = 1.0572068369257646Pa.s, den = 982.291799kg/m^3
p = 10000000.0Pa, T = 400K, vis = 0.07505289708588177Pa.s, den = 954.218799kg/m^3
p = 10000000.0Pa, T = 500K, vis = 0.006981110014281144Pa.s, den = 898.072799kg/m^3

NOTE (2026-10-09): the five lines above are the values of the CORRELATIONS
themselves (with `b3 = 0.00511938` and the 273.15 K offset), i.e. what
get_viscosity() / get_density() return. NOTE (2026-10-10): `__main__` prints the
values of the built Interp2 table instead -- that table is sampled on a uniform
grid, so for a steep function such as the viscosity its numbers differ slightly
from the correlation (density, being linear in P and T, matches exactly). The
values that used to be here came from `b3 = int(0.00511938)` (truncated to 0,
which annihilated the pressure term) and from the `(temp - 273.5)` typo in
get_density; in particular the old T=300K entry (vis=97.294) was WRONG --
the correlation gives ~177.87.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from math import log, exp


from zmlx.exts import Interp2, FluDef


def create(t_min=270, t_max=1000, p_min=1e6, p_max=40e6, name=None,
           specific_heat=None):
    def get_density(pressure, temp):
        """
        Nourozieh, H., et al. (2015). "Density and Viscosity of Athabasca Bitumen Samples at Temperatures up to 200° C and Pressures up to 10 MPa." SPE Reservoir Evaluation & Engineering 18(03): 375-386.
        """
        a1 = 1021.62  # kg*m^-3
        a2 = - 0.58976  # kg*m^-3 * C^-1
        a4 = 0.382  # 1/MPa
        a5 = 0.00283  # C^-1
        # ⚠️ 两处的 Kelvin->Celsius 偏移必须一致，且只能是 273.15：
        #    这里曾把 alpha 写成 (temp - 273.5)（全仓库唯一一处 273.5），
        #    与下面 density 的 273.15 自相矛盾 —— 273.15 才是精确的换算常数。
        alpha = a4 + a5 * (temp - 273.15)  # temp = Kelvin to Celsius
        den_o = a1 + a2 * (temp - 273.15)  # temp = Kelvin to Celsius
        den = den_o + alpha * (pressure * 0.000001)  # Pressure Mpa
        return den

    def get_viscosity(pressure, temp):  # Mehrotra and Svrcek, 1986
        """
        Mehrotra, A. K. and W. Y. Svrcek (1986).
        "Viscosity of compressed athabasca bitumen." The Canadian Journal of Chemical Engineering 64(5): 844-847.
        """
        b1 = 22.8515
        b2 = -3.5784
        # ⚠️ 必须保留小数：这里曾经误写成 int(0.00511938)，被截断成 0，
        #    于是压力项整个消失 —— 粘度退化成只与温度有关（40MPa 下比真值
        #    小 13.6 倍）。见本模块 docstring 的参考值。
        b3 = 0.00511938
        A = (b1 + (b2 * log(temp))) + (b3 * (pressure * 0.000001))
        vis_oil = 0.001 * (exp(exp(A)))
        return vis_oil

    def create_density():
        den = Interp2()
        den.create(p_min, 1e6, p_max, t_min, 10, t_max, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 1e6, p_max, t_min, 10, t_max, get_viscosity)
        return vis

    if specific_heat is None:
        specific_heat = 1800

    return FluDef(den=create_density(), vis=create_viscosity(),
                  specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
    print(flu)
    for p, T in [(10e6, 280), (10e6, 300), (10e6, 350), (10e6, 400),
                 (10e6, 500)]:
        vis = flu.vis(p, T)
        den = flu.den(p, T)
        print(f'p = {p}Pa, T = {T}K, vis = {vis}Pa.s, den = {den}kg/m^3')
    try:
        from zmlx.plt import show_field2

        show_field2(flu.vis, [1e6, 40e6], [300, 1000])
        show_field2(flu.den, [1e6, 40e6], [300, 1000])
    except Exception:
        pass

    """
p = 10000000.0Pa, T = 280K, vis = 5251.493255037484Pa.s, den = 1021.593999kg/m^3
p = 10000000.0Pa, T = 300K, vis = 177.86679222419696Pa.s, den = 1010.364799kg/m^3
p = 10000000.0Pa, T = 350K, vis = 1.0572068369257646Pa.s, den = 982.291799kg/m^3
p = 10000000.0Pa, T = 400K, vis = 0.07505289708588177Pa.s, den = 954.218799kg/m^3
p = 10000000.0Pa, T = 500K, vis = 0.006981110014281144Pa.s, den = 898.072799kg/m^3

NOTE (2026-10-09): the five lines above are the values of the CORRELATIONS
themselves (with `b3 = 0.00511938` and the 273.15 K offset), i.e. what
get_viscosity() / get_density() return. NOTE (2026-10-10): `__main__` prints the
values of the built Interp2 table instead -- that table is sampled on a uniform
grid, so for a steep function such as the viscosity its numbers differ slightly
from the correlation (density, being linear in P and T, matches exactly). The
values that used to be here came from `b3 = int(0.00511938)` (truncated to 0,
which annihilated the pressure term) and from the `(temp - 273.5)` typo in
get_density; in particular the old T=300K entry (vis=97.294) was WRONG --
the correlation gives ~177.87.
    """
