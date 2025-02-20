"""
说明：
    zmlx.fluid.co2_liq需要用到第三方的库，可能会没有安装，因此，这里建立一个数据存档
"""
from zml import Seepage
from zmlx.fluid.co2_liq import create

t_min = 270
t_max = 289
p_min = 1.0e6
p_max = 20.0e6


def save():
    flu = create(t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max, name='co2')
    flu.save('co2_liq_270_289_1_20.txt')


def show():
    flu = Seepage.FluDef(path='co2_liq_270_289_1_20.txt')
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2
        show_field2(flu.den, xr=[p_min, p_max], yr=[t_min, t_max])
        show_field2(flu.vis, xr=[p_min, p_max], yr=[t_min, t_max])
    except:
        pass


if __name__ == '__main__':
    save()
    show()
