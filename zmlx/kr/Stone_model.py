import numpy as np


def stone(sirg=0.02, sirw=0.2):
    sat = np.arange(0, 1.001, 0.001)
    model = np.zeros(shape=(len(sat), 3))
    for i in range(len(sat)):
        model[i, 0] = sat[i]
        if sat[i] > sirw:
            krW = ((sat[i] - sirw) / (1 - sirw)) ** 4.5
            model[i, 1] = max(min(krW, 1), 0)
        else:
            model[i, 1] = 0

    for i in range(len(sat)):
        if sat[i] > sirg:
            krG = ((sat[i] - sirg) / (1 - sirw)) ** 3.5
            model[i, 2] = max(min(krG, 1), 0)
        else:
            model[i, 2] = 0
    return model


if __name__ == '__main__':
    data = stone()
    vs = data[:, 0]
    kg = data[:, 1]
    kw = data[:, 2]
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
