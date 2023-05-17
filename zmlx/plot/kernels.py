# -*- coding: utf-8 -*-


def plot(ax, *args, **kwargs):
    """
    利用给定的x，y来画一个二维的曲线，并且添加到给定的坐标轴ax上
    """
    return ax.plot(*args, **kwargs)


def tricontourf(ax, x=None, y=None, z=None, ipath=None, ix=None, iy=None, iz=None,
                triangulation=None, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]
        if iz is not None:
            z = data[:, iz]

    if triangulation is None:
        return ax.tricontourf(x, y, z, levels=levels, cmap=cmap, antialiased=True)
    else:
        return ax.tricontourf(triangulation, z, levels=levels, cmap=cmap, antialiased=True)


"""
用于绘图的内核函数
对于内核函数，规定其第一个参数，一定需要是一个fig.axes类的对象，将在这个坐标轴上绘图
"""
kernels = {'plot': plot, 'tricontourf': tricontourf}
