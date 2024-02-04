from zmlx.alg.linspace import linspace


def vanG_function(p0=10e5, srw=0.4, n=0.45, count=100):
    """
    利用van Genuchten函数创建毛细压力；
    """

    vs = linspace(0.0, 1.0, count)
    a = - (1 / n)
    b = 1 - n
    cap = []
    for s in vs:
        if s > srw:
            p = (((s - srw) / (1 - srw)) ** a - 1) ** b
            k = - p0 * p
            cap.append(max(k, -10e6))
        else:
            cap.append(0)
    return vs, cap


def _test1():
    # create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    vs, cap = vanG_function(p0=10e5, srw=0.4, n=0.45, count=100)
    for i in range(len(vs)):
        print(vs[i], cap[i])

    import numpy as np
    from zmlx.ui.GuiBuffer import plot

    def f(fig):
        ax = fig.subplots()
        ax.plot(vs, cap)

    plot(f)


if __name__ == '__main__':
    _test1()