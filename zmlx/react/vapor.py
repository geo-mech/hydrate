# -*- coding: utf-8 -*-
"""
定义水气液转化临界曲线
"""

from math import exp
from zml import Reaction
from zmlx.alg.make_index import make_index


def create(ivap, iwat, fa_t, fa_c):
    """
    建立水蒸气和水之间的相变
        ivap: 水蒸气的ID；iwat水的ID
    """
    react = Reaction()
    # 使用Antoine 公式，实际上这个温度范围可能已经超过了该公式的适用范围
    vt = [float(i) for i in range(290, 700)]
    vp = [exp(9.3876 - 3826.36 / (t - 45.47)) * 1.0e6 for t in vt]
    react.set_p2t(vp, vt)
    react.temp = 273 + 100
    react.dheat = 2.26e6
    react.set_t2q([-300, 0, 300], [300, 0, -300])
    react.add_component(index=make_index(ivap), weight=-1, fa_t=fa_t, fa_c=fa_c)
    react.add_component(index=make_index(iwat), weight=1, fa_t=fa_t, fa_c=fa_c)
    return react


def __compare():
    """
    参考文献：Wagner, W.; Pruss, A., The IAPWS Formulation 1995 for the Thermodynamic Properties of Ordinary Water Substance for General
        and Scientific Use, J. Phys. Chem. Ref. Data, 2002, 31, 2, 387-535, https://doi.org/10.1063/1.1461829 .
    """
    from zmlx.plot import plot2

    vt = [float(i) for i in range(290, 700)]
    vp = [exp(9.3876 - 3826.36 / (t - 45.47)) * 1.0e6 for t in vt]
    vt1 = [455, 460, 465, 470, 475, 480, 485, 490, 495, 500, 505, 510, 515, 520, 525, 530, 535, 540, 545,
           550, 555, 560, 565, 570, 575, 580, 585, 590, 595, 600]

    vp1 = [1.0462e6, 1.1709e6, 1.3069e6, 1.4551e6, 1.6160e6, 1.7905e6, 1.9792e6, 2.1831e6, 2.4028e6, 2.6392e6, 2.8931e6,
           3.1655e6, 3.4571e6, 3.7690e6, 4.1019e6, 4.4569e6, 4.8349e6, 5.2369e6, 5.6640e6,
           6.1172e6, 6.5976e6, 7.1062e6, 7.6444e6, 8.2132e6, 8.8140e6, 9.4480e6, 10.117e6, 10.821e6, 11.563e6, 12.345e6]

    d3 = {'name': 'plot', 'args': [vt1, vp1], 'kwargs': {'c': 'b'}}
    d4 = {'name': 'plot', 'args': [vt, vp], 'kwargs': {'c': 'r'}}
    plot2(xlabel='x', ylabel='y', data=(d3, d4))


if __name__ == '__main__':
    __compare()
