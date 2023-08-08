from zmlx.alg.linspace import linspace


def create_fracture_kr():
    """
    立方定律，导流的能力和裂缝开度的3次方成正比
    """
    vs = linspace(0.0, 10.0, 1000)
    kr = [s ** 3 for s in vs]
    return vs, kr


if __name__ == '__main__':
    from zmlx.plt.plotxy import plotxy

    x, y = create_fracture_kr()
    plotxy(x, y)
