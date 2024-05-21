import os

from zmlx.filesys.join_paths import join_paths
from zmlx.fluid.from_file import from_file


def data_file():
    return join_paths(os.path.dirname(__file__), 'data.txt')


def create(t_min=261, t_max=329, p_min=2.0e6, p_max=99.0e6, name=None):
    """
    创建ch4的定义.
    """
    return from_file(fname=join_paths(os.path.dirname(__file__), 'data.txt'),
                     t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max, name=name, specific_heat=2225.062)


def test():
    t_min = 261
    t_max = 329
    p_min = 2.0e6
    p_max = 99.0e6
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max)
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2
        show_field2(flu.den, [p_min, p_max], [t_min, t_max], caption='density')
        show_field2(flu.vis, [p_min, p_max], [t_min, t_max], caption='viscosity')
    except:
        pass


if __name__ == '__main__':
    from zmlx.ui import gui

    gui.execute(test, close_after_done=False)
