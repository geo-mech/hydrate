"""H2O 气相流体属性（基于 NIST 数据表）.

Modified by Claude, 2026-08-12
"""
import os

from zmlx.exts import Interp2, FluDef


def create(name=None):
    # 水蒸气的比热参考：
    # https://zhidao.baidu.com/question/304769103441864644.html
    return FluDef(
        den=Interp2(path=os.path.join(os.path.dirname(__file__), 'den.txt')),
        vis=Interp2(path=os.path.join(os.path.dirname(__file__), 'vis.txt')),
        specific_heat=1850.0, name=name)


create_flu = create

if __name__ == '__main__':
    flu = create_flu()
    print(flu)
    try:
        from zmlx.plt import show_field2

        show_field2(flu.den, [1e6, 20e6], [270, 290])
        show_field2(flu.vis, [1e6, 20e6], [270, 290])
    except Exception:
        pass
