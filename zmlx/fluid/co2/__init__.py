import os
import warnings

from zml import TherFlowConfig, Interp2


def create():
    """
    创建CO2数据；压力范围：1MPa到30MPa；温度范围250K到300K
    """
    # Co2的比热:
    # 参考：https://baike.baidu.com/item/%E4%BA%8C%E6%B0%A7%E5%8C%96%E7%A2%B3/349143
    #
    specific_heat = 2844.8
    return TherFlowConfig.FluProperty(den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
                                      vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
                                      specific_heat=specific_heat)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.den, [1e6, 20e6], [270, 290])
        show_field2(flu.vis, [1e6, 20e6], [270, 290])
    except:
        pass
