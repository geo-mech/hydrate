from zmlx.fluid.nist.co2 import create


def test1():
    from zmlx.plt import show_flu_def
    t_min = 274
    t_max = 329
    p_min = 1.0e6
    p_max = 49.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max, name='co2_liq')
    print(flu)
    show_flu_def(flu, [p_min, p_max], [t_min, t_max], caption='Fluid Definition')


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test1, close_after_done=False)
