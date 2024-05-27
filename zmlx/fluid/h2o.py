"""
定义水的参数   by 张召彬
"""

import math
import warnings

from zml import Interp2, Seepage


def create(t_min=272.0, t_max=300.0, p_min=1e6, p_max=40e6,
           name=None,
           density=None, viscosity=None,
           specific_heat=4200.0):
    """
    创建液体水的参数

    水的比热：参考：
    https://zhidao.baidu.com/question/2159847.html

    水的比热容在25℃时，大约是4.2×10³ J/（kg℃)，比其它液体普遍较高。

    比热容（Specific Heat Capacity，符号c），简称比热，亦称比热容量，
    是热力学中常用的一个物理量，表示物体吸热或散热能力。比热容越大，
    物体的吸热或散热能力越强。它指单位质量的某种物质升高或下降单位
    温度所吸收或放出的热量。其国际单位制中的单位是焦耳每千克开尔文[J/(
    kg · K )]，即令1公斤的物质的温度上升1开尔文所需的能量。
    """

    assert 269 < t_min < t_max < 350
    assert 0.01e6 < p_min < p_max < 50e6

    def get_density(P, T):
        T = max(t_min, min(t_max, T))
        return 999.8 * (1.0 + (P / 2000.0E6)) * (1.0 - 0.0002 * math.pow((T - 277.0) / 5.6, 2))

    def get_viscosity(P, T):
        T = max(t_min, min(t_max, T))
        return 2.0E-6 * math.exp(1808.5 / T)

    def create_density():
        den = Interp2()
        den.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(p_min, 0.1e6, p_max, t_min, 1, t_max, get_viscosity)
        return vis

    if density is not None:
        assert 900.0 <= density <= 1100.0

    if viscosity is not None:
        assert 1.0e-5 <= viscosity <= 1.0e-2

    return Seepage.FluDef(den=create_density() if density is None else density,
                          vis=create_viscosity() if viscosity is None else viscosity,
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


def show_all():
    from zmlx.plt.show_field2 import show_field2
    flu = create()
    show_field2(flu.den, [4e6, 15e6], [274, 290], caption='den')
    show_field2(flu.vis, [4e6, 15e6], [274, 290], caption='vis')


if __name__ == '__main__':
    from zmlx.ui import gui
    gui.execute(show_all, close_after_done=False)
