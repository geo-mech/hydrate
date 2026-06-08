from zmlx.fig import *


def test_2():
    import numpy as np
    from zmlx.geometry.dfn2 import dfn2 as make_fractures

    x = np.linspace(-5, 5, 30)
    y = np.linspace(-5, 5, 30)
    x, y = np.meshgrid(x, y)
    z = np.sin(np.sqrt(x ** 2 + y ** 2))
    a = np.linspace(-4, 15, 100)
    b = np.sin(a)
    fractures = make_fractures(
        lr=[2, 10], ar=[0, 1], p21=4,
        xr=[-5, 17],
        yr=[5, 17.5], l_min=0.2
    )

    items = [
        cont(x, y, z, cmap='coolwarm'),
        tric(x.flatten() + 12, y.flatten(), z.flatten(),
             cmap='coolwarm'),
        cbar(clim=(-1, 1), label='label', title='title',
             shrink=0.8, cmap='coolwarm'),
        comb(
            curve(a, b),
            curve(a, b + 1),
            curve(a, b + 2),
        ),
        dfn2(fractures),
        comb(
            xlabel('x/m'),
            ylabel('y/m'),
            comb(
                aspect('equal'),
                xlim([-3, 16]),
            )
        ),
    ]
    plot2d(*items)


if __name__ == '__main__':
    test_2()
