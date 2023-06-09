# -*- coding: utf-8 -*-


from zmlx.alg.linspace import linspace


def create_krf(faic=0.2, n=2.0):
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
    vs = linspace(0.0, 1.0, 100)
    kr = []
    for s in vs:
        if s <= faic:
            kr.append(0)
        else:
            k = ((s - faic) / (1 - faic)) ** n
            kr.append(max(0.0, min(1.0, k)))
    return vs, kr


if __name__ == '__main__':
    x, y = create_krf(0.05, 3)
    print(x)
    print(y)
    try:
        def f(fig):
            ax = fig.subplots()
            ax.plot(x, y)
        from zml import plot
        plot(f)
    except:
        pass
