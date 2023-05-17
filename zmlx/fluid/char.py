# -*- coding: utf-8 -*-


from zml import TherFlowConfig


def create_flu(den=1100):
    """
    Data from Maryelin.
        密度在1100到1800之间
    """
    vis = 1.0e30
    specific_heat = 1380
    return TherFlowConfig.FluProperty(den=den, vis=vis, specific_heat=specific_heat)


if __name__ == '__main__':
    print(create_flu())
