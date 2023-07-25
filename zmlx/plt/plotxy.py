from zml import gui, plot


def plotxy(x=None, y=None, ipath=None, ix=None, iy=None, caption=None, gui_only=False,
           title=None, fname=None, dpi=300, xlabel='x', ylabel='y', clear=True):
    """
    利用给定的x，y来画一个二维的曲线
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

    def f(fig):
        ax = fig.subplots()
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        ax.plot(x, y)

    if not gui_only or gui.exists():
        plot(kernel=f, caption=caption, clear=clear, fname=fname, dpi=dpi)
