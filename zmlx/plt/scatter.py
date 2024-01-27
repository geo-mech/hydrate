from zmlx.ui.GuiBuffer import plot


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

    plot(kernel=kernel, caption=caption, clear=True)
