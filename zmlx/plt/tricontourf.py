from zml import plot, gui


def tricontourf(x=None, y=None, z=None, ipath=None, ix=None, iy=None, iz=None, caption=None, gui_only=False,
                title=None, triangulation=None, fname=None, dpi=300, levels=20, cmap='coolwarm'):
    """
    利用给定的x，y，z来画一个二维的云图
    """
    if gui_only and not gui.exists():
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

    if not gui_only or gui.exists():
        plot(kernel=f, caption=caption, clear=True, fname=fname, dpi=dpi)

