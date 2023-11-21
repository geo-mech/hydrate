import os

from zml import Interp2
from zmlx.config.TherFlowConfig import TherFlowConfig


def create(name=None):
    # 水蒸气的比热参考：
    # https://zhidao.baidu.com/question/304769103441864644.html
    return TherFlowConfig.FluProperty(den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
                                      vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
                                      specific_heat=1850.0, name=name)


create_flu = create

if __name__ == '__main__':
    flu = create_flu()
    print(flu)
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.den, [1e6, 20e6], [270, 290])
        show_field2(flu.vis, [1e6, 20e6], [270, 290])
    except:
        pass
