# -*- coding: utf-8 -*-


import zml


def scatter(items=None, get_val=None, x=None, y=None, z=None, c=None, get_pos=None, caption='scatter',
            alpha=1.0, cb_label=None, cmap='coolwarm'):
    if x is None or y is None or z is None:
        if get_pos is None:
            def get_pos(item):
                return item.pos
        vpos = [get_pos(item) for item in items]
        x = [pos[0] for pos in vpos]
        y = [pos[1] for pos in vpos]
        z = [pos[2] for pos in vpos]
    if c is None:
        assert get_val is not None
        c = [get_val(item) for item in items]

    def kernel(fig):
        ax = fig.add_subplot(projection='3d')
        ax.set_aspect('auto')
        ax.set_xlabel('x/m')
        ax.set_ylabel('y/m')
        ax.set_zlabel('z/m')
        sc = ax.scatter(x, y, z, c=c, marker='o', cmap=cmap, alpha=alpha)
        cb = fig.colorbar(sc, ax=ax)
        if cb_label is not None:
            cb.set_label(cb_label)

    zml.plot(kernel=kernel, caption=caption, clear=True)


def tricontourf(x=None, y=None, z=None, ipath=None, ix=None, iy=None, iz=None, caption=None, gui_only=False,
                title=None, triangulation=None, fname=None, dpi=300, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if gui_only and not zml.gui.exists():
        return

    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]
        if iz is not None:
            z = data[:, iz]

    def f(fig):
        ax = fig.subplots()
        ax.set_aspect('equal')
        ax.set_xlabel('x/m')
        ax.set_ylabel('y/m')
        if title is not None:
            ax.set_title(title)
        if triangulation is None:
            contour = ax.tricontourf(x, y, z, levels=levels, cmap=cmap, antialiased=True)
        else:
            contour = ax.tricontourf(triangulation, z, levels=levels, cmap=cmap, antialiased=True)
        fig.colorbar(contour, ax=ax)

    if not gui_only or zml.gui.exists():
        zml.plot(kernel=f, caption=caption, clear=True, fname=fname, dpi=dpi)


def plotxy(x=None, y=None, ipath=None, ix=None, iy=None, caption=None, gui_only=False,
           title=None, fname=None, dpi=300, xlabel='x', ylabel='y', clear=True):
    """
    利用给定的x，y来画一个二维的曲线
    """
    if gui_only and not zml.gui.exists():
        return

    if ipath is not None:
        import numpy as np
        data = np.loadtxt(ipath, float)
        if ix is not None:
            x = data[:, ix]
        if iy is not None:
            y = data[:, iy]

    def f(fig):
        ax = fig.subplots()
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        ax.plot(x, y)

    if not gui_only or zml.gui.exists():
        zml.plot(kernel=f, caption=caption, clear=clear, fname=fname, dpi=dpi)
