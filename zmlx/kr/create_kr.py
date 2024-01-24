from zmlx.alg.linspace import linspace


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


def _test1():
    # create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5, count=1000)
    for i in range(len(vs)):
        print(vs[i], kg[i], kw[len(vs)-1-i])

    import numpy as np
    from zmlx.ui.GuiBuffer import gui, plot

    def f(fig):
        ax = fig.subplots()
        ax.plot(vs, kg)
        ax.plot(1 - np.asarray(vs), kw)

    plot(f)


if __name__ == '__main__':
    _test1()
