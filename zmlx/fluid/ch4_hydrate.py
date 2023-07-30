"""
定义甲烷水合物的基本参数
"""

import warnings

from zml import data_version, TherFlowConfig

"""
甲烷水合物的比热随着温度和压力略有变化，但是变化的幅度很小，所以可以视为常数:
参考：
https://pubs.usgs.gov/fs/2007/3041/pdf/FS-2007-3041.pdf

大约2100左右

by 张召彬 
"""


def create():
    if data_version.ch4_hydrate >= 221024:
        specific_heat = 2100.0
    else:
        # 之前随手写的，错了
        specific_heat = 1000.0
    return TherFlowConfig.FluProperty(den=919.7,
                                      vis=1.0e30,
                                      specific_heat=specific_heat)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create_flu()
    print(flu)
