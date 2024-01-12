from zml import Seepage
import os


def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


def load(key, name=None):
    """
    导入流体的定义。如果给定name，则替换name
    """
    fname = get_path(key)
    if os.path.isfile(fname):
        flu = Seepage.FluDef(path=fname)
        if name is not None:
            flu.name = name
        return flu


def load_co2_liq_270_289_1_20(name=None):
    return load('co2_liq_270_289_1_20.txt', name=name)


def show(flu, p_min=1e6, p_max=20e6, t_min=270, t_max=290):
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2
        show_field2(flu.den, xr=[p_min, p_max], yr=[t_min, t_max])
        show_field2(flu.vis, xr=[p_min, p_max], yr=[t_min, t_max])
    except:
        pass


if __name__ == '__main__':
    show(load_co2_liq_270_289_1_20())
