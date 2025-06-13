"""
定义CO2水合物的基本参数

参考文献：
Anderson G K, 2003.. The Journal of Chemical Thermodynamics, 35(7): 1171–1183. DOI:10.1016/S0021-9614(03)00093-4.
Zhou X, Fan S, Liang D, et al., 2008. . Energy Conversion and Management, 49(8): 2124–2129. DOI:10.1016/j.enconman.2008.02.006.

"""

import zmlx.react.hydrate as hydrate
from zml import Interp1
from zmlx.alg.interp import interp1

# 温度
vt = [265, 273.25, 274.33, 275.6, 276.12, 276.63, 277.34, 278.09, 279.32,
      280.02,
      280.64, 281.25, 281.86, 282.19, 282.53, 282.81, 283.14, 283.38, 283.67,
      284.01,
      284.2, 284.44]

# 压力
vp = [952740, 1152740, 1263150, 1479310, 1586770, 1694230, 1802670,
      2016120, 2546270, 2759470, 2972170, 3708620, 4549820, 6332280,
      8219490, 10001700, 12203200, 16394400, 21214300, 27291500, 30644500,
      34835700]


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


def get_mg_vs_mh(nh=5.75):
    """
    返回1kg水合物分解之后产生的气体的质量(kg)

    水合物数Nh的默认值 5.75
        参考 https://www.science.org/doi/10.1126/sciadv.aao6588
            Long-term viability of carbon sequestration in deep-sea sediments (的附件)
        当Nh=5.75的时候，返回0.298
    """

    # 在上一个版本中，返回固定值0.286 (before 2024-2-17)
    return 44.01 / (18.015 * nh + 44.01)


def get_mol_mass(nh=5.75):
    """
    摩尔质量.
        Nh=5.75的时候，返回0.147
    """
    return (18.015 * nh + 44.01) / 1.0e3


def get_dheat(nh=5.75):
    """
    分解1kg水合物所需要消耗的热量.

    分解1mol水合物消耗的热量大约为60KJ
        参考 https://www.science.org/doi/10.1126/sciadv.aao6588
            Long-term viability of carbon sequestration in deep-sea sediments (的附件)
    """
    # return 394225.0  (旧版本)
    return 60.0e3 / get_mol_mass(nh=nh)  # 默认返回 406514.3


def create(gas, wat, hyd, fa_t=None, fa_c=None, dissociation=True,
           formation=True, nh=5.75):
    """
    创建一个水合物反应(平衡态的反应，反应的速率给的非常大)
    by 张召彬

    注意：
        返回一个dict，包含了反应的所有的信息。此dict定义的data可以在
        zmlx.react.alg.add_reaction中使用，将反应添加到Seepage中
    """
    return hydrate.create(
        vp=vp, vt=vt, temp=273.15, heat=get_dheat(nh),
        mg=get_mg_vs_mh(nh),
        gas=gas, liq=wat, hyd=hyd, fa_t=fa_t, fa_c=fa_c,
        dissociation=dissociation, formation=formation
    )


if __name__ == '__main__':
    # 和甲烷水合物比较(总的来说，各个参数都在接近的的量级)
    from zmlx.react.ch4_hydrate import vp as vp1, vt as vt1
    from zmlx.react.ch4_hydrate import get_mg_vs_mh as get_mg
    from zmlx.react.ch4_hydrate import get_dheat as get_dh

    print(f'mg = {get_mg_vs_mh()}, {get_mg()}')
    print(f'dh = {get_dheat()}, {get_dh()}')

    d3 = {'name': 'plot', 'args': [vt1, vp1], 'kwargs': {'c': 'b'}}
    d4 = {'name': 'plot', 'args': [vt, vp], 'kwargs': {'c': 'r'}}
    from zmlx.plt.fig2 import plot2

    plot2(xlabel='x', ylabel='y', data=(d3, d4))
