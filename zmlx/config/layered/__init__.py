"""
一种将储层视为多个层的配置方式。基于此，模拟压裂和排采的过程。

将储层视为一系列二维的Layer的叠加，并添加虚拟的Face来建立这些Layer之间的联系（流体的传递和压力的平衡）.
另外，裂缝也是虚拟的Face.

考虑计算的流程：

1. 计算每一个Layer内的流动过程.
2. 计算Layer之间的流体的平衡.
"""

from zmlx.config.layered._iterate import iterate
from zmlx.config.layered._group import group

__all__ = ['iterate', 'group']
