"""
@author: Maryelin

Modify by ZZB @2024.1.10   Copy from zmlx/conf/CO2_liq.py
"""

from zml import Interp2, Seepage
from zmlx.fluid.conf.liqu_density.co2 import liq_den_co2
from zmlx.fluid.conf.liqu_viscosity.co2 import liq_vis_co2


def create(t_min=270, t_max=285, p_min=1.0e6, p_max=20.0e6, name=None):
    """
    创建液态co2的定义.
    """
    assert 250 <= t_min < t_max <= 320
    assert 0.01e6 <= p_min < p_max <= 30.0e6

    def gas_den(P, T):
        return liq_den_co2(P, T)

    def create_density():
        den = Interp2()
        den.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_den)
        return den

    def gas_vis(P, T):
        return liq_vis_co2(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 1e6, p_max, t_min, 1, t_max, gas_vis)
        return vis

    specific_heat = 2303.56

    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat,
                          name=name)


def test1():
    t_min = 260
    t_max = 289
    p_min = 1.0e6
    p_max = 20.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max)
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.den, [p_min, p_max], [t_min, t_max])
        show_field2(flu.vis, [p_min, p_max], [t_min, t_max])
    except:
        pass


def test2():
    """
    The only difference of test2 and test1 is the t_max

    in test1, t_max=289, it works, but in test2, t_max=291, it case an error:

        z array must not contain non-finite values within the triangulation
    """
    t_min = 260
    t_max = 291   # Now, z array must not contain non-finite values within the triangulation
    p_min = 1.0e6
    p_max = 20.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max)
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.den, [p_min, p_max], [t_min, t_max])
        show_field2(flu.vis, [p_min, p_max], [t_min, t_max])
    except:
        pass


if __name__ == '__main__':
    test1()
