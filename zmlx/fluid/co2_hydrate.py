"""
定义二氧化碳水合物的基本参数
"""

import warnings

from zml import TherFlowConfig


def create():
    # print('Warning: Carbon dioxide hydrate parameters not found, replaced by methane hydrate')
    specific_heat = 2100.0
    return TherFlowConfig.FluProperty(den=919.7,
                                      vis=1.0e30,
                                      specific_heat=specific_heat)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
    print(flu)
