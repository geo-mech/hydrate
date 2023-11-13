from zmlx.ui.GuiBuffer import gui, plot


def contourf(x=None, y=None, z=None, caption=None, gui_only=False,
             title=None, fname=None, dpi=300, levels=20, cmap='coolwarm',
             xlabel='x', ylabel='y', aspect='equal', clabel=None):
    """
    利用给定的x，y，z来画一个二维的云图.
    """
    if gui_only and not gui.exists():
        return

    def f(fig):
        ax = fig.subplots()

        if aspect is not None:
            ax.set_aspect(aspect)

        if xlabel is not None:
            ax.set_xlabel(xlabel)

        if ylabel is not None:
            ax.set_ylabel(ylabel)

        if title is not None:
            ax.set_title(title)

        ct = ax.contourf(x, y, z, levels=levels, cmap=cmap, antialiased=True)

        cbar = fig.colorbar(ct, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    plot(kernel=f, caption=caption, clear=True, fname=fname, dpi=dpi)
