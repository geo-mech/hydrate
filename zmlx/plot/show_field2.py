# -*- coding: utf-8 -*-


from zmlx.plot.plot2 import plot2


def show_field2(f, xr, yr, caption=None):
    """
    显示一个二维的场，用于测试
    """
    x = []
    y = []
    z = []

    va = [xr[0] + (xr[1] - xr[0]) * i * 0.01 for i in range(101)]
    vb = [yr[0] + (yr[1] - yr[0]) * i * 0.01 for i in range(101)]

    for a in va:
        for b in vb:
            x.append(a)
            y.append(b)
            z.append(f(a, b))

    d = {'name': 'tricontourf',
         'kwargs': {'x': x,
                    'y': y,
                    'z': z,
                    'levels': 30},
         'has_colorbar': True}

    plot2(caption=caption, gui_only=False, title=None, fname=None, dpi=300,
          xlabel='x', ylabel='y', clear=True,
          data=(d,))
