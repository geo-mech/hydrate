"""
盐度对水合物平衡温度的影响

by 李宇轩 2022-12-23

todo:
    添加参考文献. (并在此文件夹放pdf)

关于盐度，需要特别说明，在程序计算的时候，盐度一定指的是质量浓度，
而非体积浓度 (即盐的质量，除以溶液的质量)
"""

from zmlx.alg.interp import interp1
from zmlx.react.ch4_hydrate import get_p as ch4_get_p_
from zmlx.react.ch4_hydrate import get_t as ch4_get_t_

# 15MPa (不同盐度下，平衡温度的变化幅度)
vs = [0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08,
      0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18,
      0.19, 0.2]
vt = [0, -0.220, -0.493, -0.818, -1.194, -1.618, -2.087, -2.6,
      -3.154, -3.745, -4.37, -5.026, -5.709, -6.415, -7.141,
      -7.883, -8.635, -9.396, -10.16, -10.922, -11.679]


def get_ch4_hydrate_t(p, s=0.0):
    """
    在盐度为s的情况下，给定压力下的平衡温度
    """
    return ch4_get_t_(p) + interp1(x=vs, y=vt, xq=s)


def get_ch4_hydrate_p(t, s=0.0):
    """
    在盐度为s的情况下，给定温度下的平衡压力
    """
    return ch4_get_p_(t - interp1(x=vs, y=vt, xq=s))


def test_1():
    p1 = 10e6
    s = 0.1
    t1 = get_ch4_hydrate_t(p1, s)
    p2 = get_ch4_hydrate_p(t1, s)
    print(f'p1 = {p1}, t1 = {t1}, p2 = {p2}')


# 10MPa
__s2 = [0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08,
        0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18,
        0.19, 0.2]
__dT2 = [0, -0.247, -0.543, -0.889, -1.282, -1.721, -2.204,
         -2.729, -3.293, -3.894, -4.53, -5.198, -5.894, -6.617,
         -7.362,
         -8.127, -8.908, -9.703, -10.507, -11.317, -12.130]

# 用以导出的数据：其它所有数据都不要使用
data = (vs, vt)


def test_2():
    from zmlx import plot2

    plot2(data=[{'name': 'plot', 'args': [vs, vt]},
                {'name': 'plot', 'args': [__s2, __dT2]}])


if __name__ == '__main__':
    test_2()
