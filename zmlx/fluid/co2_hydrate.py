"""
定义二氧化碳水合物的基本参数
"""

import zmlx.alg.sys as warnings

from zml import Seepage


def create(name=None, den=1112.0, specific_heat=2190.0):
    """
    密度：
        1112kg/m^3
        参考 https://www.science.org/doi/10.1126/sciadv.aao6588
            Long-term viability of carbon sequestration in deep-sea sediments
        注：
        之前的版本，拷贝自甲烷水合物，为919.7

    比热：
        默认2190
        参考 https://www.science.org/doi/10.1126/sciadv.aao6588
            Long-term viability of carbon sequestration in deep-sea sediments
        注：
        之前的版本，拷贝自甲烷水合物，为2100

    """
    return Seepage.FluDef(den=den,  # 之前的版本，拷贝自甲烷水合物，为919.7
                          vis=1.0e30,
                          specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning,
                  stacklevel=2)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
    print(flu)
