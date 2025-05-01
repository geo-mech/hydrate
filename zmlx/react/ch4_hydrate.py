"""
定义甲烷水合物的基本参数
"""

import zmlx.react.hydrate as hydrate
from zml import Interp1
from zmlx.alg.interp import interp1

# 温度压力曲线：取自Tough+Hydrate的手册
vt = [148.714, 154.578, 159.889, 166.418, 174.827, 183.458, 192.199, 200.277, 207.026, 213.887, 222.739, 231.259,
      236.017, 241.438, 247.746, 253.278, 258.257, 261.134, 265.007, 267.663, 270.207, 272.752, 275.408, 278.728,
      281.494, 284.703, 287.69, 289.461, 291.784, 293.776, 295.325, 297.095, 299.198, 302.185, 304.066, 305.726,
      307.497, 309.488, 311.48, 313.14, 316.017, 317.566, 319.004, 320, 320.221]

vp = [5262.24, 8054.63, 11965.9, 18591.3, 32551.1, 56148.2, 94000.9, 147142, 209015, 292504, 434544, 617269, 738443,
      890026, 1.10525e+06, 1.34212e+06, 1.57001e+06, 1.73008e+06, 1.96429e+06, 2.16456e+06, 2.34989e+06, 2.57021e+06,
      3.23978e+06, 4.56786e+06, 6.11232e+06, 8.68254e+06, 1.23335e+07, 1.5089e+07, 2.01908e+07, 2.60274e+07,
      3.16053e+07, 3.95423e+07, 5.13549e+07, 7.24068e+07, 8.85833e+07, 1.05184e+08, 1.23967e+08, 1.46104e+08,
      1.73484e+08, 1.98446e+08, 2.57728e+08, 3.0149e+08, 3.57991e+08, 3.97448e+08, 4.47894e+08]


def get_p(t):
    """
    返回给定的温度对应的压力
    """
    return interp1(vt, vp, t)


def get_t(p):
    """
    返回给定压力对应的温度
    """
    return interp1(vp, vt, p)


def create_t2p():
    return Interp1(x=vt, y=vp).to_evenly_spaced(300)


def create_p2t():
    return Interp1(x=vp, y=vt).to_evenly_spaced(300)


def get_mg_vs_mh(Nh=6.0):
    """
    返回1kg水合物分解之后产生的甲烷气体的质量(kg);

        When Nh=6, Return 0.129
        When Nh=5, Return 0.151
    """
    return 16.0 / (18.0 * Nh + 16.0)


def get_dheat(Nh=6.0):
    """
    分解1kg水合物所需要消耗的热量
    ---
    2022-10-29
    分解1mol的水合物，所需要消耗的热量应该为54.2kJ，之前写成了62.8（也不知道是从哪里得到的数据）
    ---
        When Nh=6, Return 437096.77
        When Nh=5, Return 511320.75
    """
    return (54.2e3 / 16.0E-3) * get_mg_vs_mh(Nh)


def create(gas, wat, hyd, fa_t=None, fa_c=None, dissociation=True, formation=True, Nh=6.0):
    """
    创建一个ch4水合物反应(平衡态的反应，反应的速率给的非常大)
    by 张召彬
    """
    return hydrate.create(vp=vp, vt=vt, temp=273.15, heat=get_dheat(Nh=Nh),
                          mg=get_mg_vs_mh(Nh=Nh),
                          gas=gas, liq=wat, hyd=hyd,
                          fa_t=fa_t, fa_c=fa_c,
                          dissociation=dissociation, formation=formation)


if __name__ == '__main__':
    print(get_dheat(6.0))
    print(get_dheat(5.0))
