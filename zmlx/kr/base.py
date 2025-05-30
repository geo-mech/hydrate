from zml import Interp1
from zmlx.alg.base import linspace


def create_fracture_kr():
    """
    立方定律，导流的能力和裂缝开度的3次方成正比
    """
    vs = linspace(0.0, 10.0, 1000)
    kr = [s ** 3 for s in vs]
    return vs, kr


def create_kr(srg=0.02, srw=0.2, ag=3.5, aw=4.5, count=100):
    """
    利用Stone模型创建气水两相的相对渗透率；
    """
    assert 1.0 <= ag <= 6.0
    assert 1.0 <= aw <= 6.0
    vs = linspace(0.0, 1.0, count)
    kg = []
    kw = []
    for s in vs:
        if s > srg:
            k = ((s - srg) / (1 - srw)) ** ag
            kg.append(max(min(k, 1), 0))
        else:
            kg.append(0)
        if s > srw:
            k = ((s - srw) / (1 - srw)) ** aw
            kw.append(max(min(k, 1), 0))
        else:
            kw.append(0)
    return vs, kg, kw


def create_krf(faic=0.2, n=2.0, as_interp=False, k_max=1.0, s_max=1.0,
               count=100):
    """
    当部分孔隙空间被水合物占据的时候，计算流体渗透率的折减. 其中faic为临界孔隙度和原始孔隙度的比值;
    返回：
        x: 流体的体积占据孔隙空间的比例
        y: 流体渗透率与原始渗透率的比值
    参考文献：
    The Mechanism of Methane Gas Migration Through the Gas Hydrate Stability Zone:
    Insights From Numerical Simulations. Eq 7
    """
    assert 0 <= faic < 0.98
    assert 1.0 <= n <= 10
    vs = linspace(0.0, s_max, count)
    kr = []
    for s in vs:
        if s <= faic:
            kr.append(0)
        else:
            k = ((s - faic) / (1 - faic)) ** n
            kr.append(max(0.0, min(k_max, k)))
    if as_interp:
        return Interp1(x=vs, y=kr)
    else:
        return vs, kr
