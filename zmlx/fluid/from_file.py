import numpy as np
from zmlx.fluid.from_data import from_data


class _Getter:
    def __init__(self, index):
        self.index = index

    def __call__(self, item):
        assert self.index < len(item)
        return item[self.index]


def from_file(fname, t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None):
    """
    从txt文件中读取数据，并且创建流体的定义. 其中文件的格式为：
        第一列： 温度 [K]
        第二列: 压力[Pa]
        第三列: 密度[kg/m^3]
        第四列: 粘性系数 [Pa.s]
    """
    data = np.loadtxt(fname=fname).tolist()
    return from_data(data=data, get_t=_Getter(0), get_p=_Getter(1),
                     get_den=_Getter(2),
                     get_vis=_Getter(3),
                     t_min=t_min, t_max=t_max,
                     p_min=p_min, p_max=p_max,
                     name=name, specific_heat=specific_heat
                     )
