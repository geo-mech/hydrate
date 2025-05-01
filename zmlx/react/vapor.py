"""
定义蒸汽和水之间的相变的反应.
    假设水的比热取 4200
    蒸汽的比热取 1850.0
那么，将1kg的水，从273+20K加热到373K，需要消耗热量
    4200*80=336000J
接下来，相变气化消耗热量
    2.26e6J
在之后，蒸汽的温度每升高100K，消耗的热量大约为
    1850*100=185000J
因此，对于常温（20度）的水，加热形成蒸汽，所需要消耗的热量，是和蒸汽的温度相关的，具体地，
产生1kg的蒸汽需要消耗的热量大约为
    336000+2.26e6+(T-373)*1850
    =2596000+(T-373)*1850
这样：
    T=400, 2645950J
    T=500, 2830950J
    T=600, 3015950J
    T=700, 3200950J
    T=800, 3385950J
    T=900, 3570950J
"""
from math import exp

from zmlx.react import melt


def get_heat_need(water_T, steam_T):
    """
    返回将1kg的T0温度的水加热并生成T1温度的蒸汽，所需要消耗的热量 (大约的，仅仅用于建模的时候使用)
    """
    E1 = 4200.0 * (273.15 + 100.0 - water_T)  # 首先，加热到100摄氏度的水
    E2 = 2.26e6  # 相变
    E3 = 1850 * (steam_T - (273.15 + 100.0))  # 蒸汽继续升温
    return E1 + E2 + E3


def create(vap, wat, fa_t=None, fa_c=None, temp_max=None):
    """
    创建水气化成为水蒸气的反应(以及其逆过程)
        ivap: 水蒸气的ID；iwat水的ID
    """
    # 使用Antoine 公式，实际上这个温度范围可能已经超过了该公式的适用范围
    if temp_max is None:
        temp_max = 700

    assert 400 <= temp_max <= 1200
    temp_max = round(temp_max)  # 液态水允许的最高的温度

    vt = [float(i) for i in range(290, temp_max)]
    vp = [exp(9.3876 - 3826.36 / (t - 45.47)) * 1.0e6 for t in vt]

    # 假设反应在373K的时候发生，那么每千克的物质，会释放
    # 大约2.26e6焦耳的热量.
    return melt.create(sol=wat, flu=vap,
                       temp=273 + 100,
                       heat=2.26e6,
                       fa_t=fa_t,
                       fa_c=fa_c,
                       vp=vp,
                       vt=vt, t2q=None)


def test_1():
    """
    参考文献：Wagner, W.; Pruss, A., The IAPWS Formulation 1995 for the Thermodynamic Properties of Ordinary Water Substance for General
        and Scientific Use, J. Phys. Chem. Ref. Data, 2002, 31, 2, 387-535, https://doi.org/10.1063/1.1461829 .
    """
    from zmlx.plt.fig2 import plot2

    vt = [float(i) for i in range(290, 1200)]
    vp = [exp(9.3876 - 3826.36 / (t - 45.47)) * 1.0e6 for t in vt]
    vt1 = [455, 460, 465, 470, 475, 480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535, 540, 545,
           550, 555, 560, 565, 570, 575, 580, 585, 590, 595, 600]

    vp1 = [1.0462e6, 1.1709e6, 1.3069e6, 1.4551e6, 1.6160e6, 1.7905e6, 1.9792e6, 2.1831e6, 2.4028e6, 2.6392e6, 2.8931e6,
           3.1655e6, 3.4571e6, 3.7690e6, 4.1019e6, 4.4569e6, 4.8349e6, 5.2369e6, 5.6640e6,
           6.1172e6, 6.5976e6, 7.1062e6, 7.6444e6, 8.2132e6, 8.8140e6, 9.4480e6, 10.117e6, 10.821e6, 11.563e6, 12.345e6]

    d3 = {'name': 'plot', 'args': [vt1, vp1], 'kwargs': {'c': 'b'}}
    d4 = {'name': 'plot', 'args': [vt, vp], 'kwargs': {'c': 'r'}}
    plot2(xlabel='x', ylabel='y', data=(d3, d4))


def test_2():
    print(get_heat_need(273.15 + 20, 400))


if __name__ == '__main__':
    test_2()
