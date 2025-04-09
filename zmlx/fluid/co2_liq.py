from zmlx.fluid.nist.co2 import create
from zmlx.plt.fig2 import show_field2
from zmlx.ui import gui


def test1():
    t_min = 274
    t_max = 289
    p_min = 1.0e6
    p_max = 20.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max)
    print(flu)
    show_field2(flu.den, [p_min, p_max], [t_min, t_max], caption='Density')
    show_field2(flu.vis, [p_min, p_max], [t_min, t_max], caption='Viscosity')


if __name__ == '__main__':
    gui.execute(test1, close_after_done=False)
