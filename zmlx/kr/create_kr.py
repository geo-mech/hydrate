from zmlx.alg.linspace import linspace


def create_kr(srg=0.02, srw=0.2, ag=3.5, aw=4.5):
    """
    利用Stone模型创建气水两相的相对渗透率；
    """
    assert 1.0 <= ag <= 6.0
    assert 1.0 <= aw <= 6.0
    vs = linspace(0.0, 1.0, 100)
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


if __name__ == '__main__':
    vs, kg, kw = create_kr(srg=0.01, srw=0.2, ag=3.5, aw=4.5)
    print(vs)
    print(kg)
    print(kw)
    try:
        def f(fig):
            ax = fig.subplots()
            ax.plot(vs, kg)
            ax.plot(vs, kw)


        from zml import plot

        plot(f)
    except:
        pass
