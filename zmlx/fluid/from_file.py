import numpy as np
from zmlx.fluid.from_data import from_data


def from_file(fname, t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None):
    """
    创建液态co2的定义.
    """
    data = np.loadtxt(fname=fname).tolist()
    return from_data(data=data,
                     get_t=lambda item: item[0],
                     get_p=lambda item: item[1],
                     get_den=lambda item: item[2],
                     get_vis=lambda item: item[3],
                     t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max,
                     name=name, specific_heat=specific_heat)
