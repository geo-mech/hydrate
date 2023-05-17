# -*- coding: utf-8 -*-
"""
定义二氧化碳水合物的基本参数
"""

from zml import TherFlowConfig


def create_flu():
    # print('Warning: Carbon dioxide hydrate parameters not found, replaced by methane hydrate')
    specific_heat = 2100.0
    return TherFlowConfig.FluProperty(den=919.7,
                                      vis=1.0e30,
                                      specific_heat=specific_heat)


if __name__ == '__main__':
    flu = create_flu()
    print(flu)
