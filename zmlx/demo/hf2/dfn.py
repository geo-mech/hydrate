import math

from zmlx.geometry.dfn2 import dfn2, get_avg_length
from zmlx.plt.show_dfn2 import show_dfn2


def create_dfn():
    """
    创建一个二维的DFN模型，用于测试
    """
    return dfn2(xr=[-40, 40], yr=[-40, 40], p21=0.3, l_min=2, lr=[10, 60], ar=[0, math.pi * 2])


def test():
    """
    测试生成dfn是否合适
    """
    fractures = create_dfn()
    print(f'average length = {get_avg_length(fractures)}')
    show_dfn2(fractures)


if __name__ == '__main__':
    test()
