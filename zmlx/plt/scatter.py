from zmlx.ui.GuiBuffer import plot


def scatter(items=None, get_val=None, x=None, y=None, z=None, c=None,
            get_pos=None,
            alpha=1.0,
            cb_label=None,
            cmap='coolwarm',
            aspect='auto', xlabel='x', ylabel='y', zlabel='z',
            **opts):
    """
    绘制三维的散点图
    """
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

    def on_figure(fig):
        ax = fig.add_subplot(111, projection='3d')
        ax.set_aspect(aspect)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_zlabel(zlabel)
        obj = ax.scatter(x, y, z, c=c, cmap=cmap, alpha=alpha)
        cbar = fig.colorbar(obj, ax=ax)
        if cb_label is not None:
            cbar.set_label(cb_label)

    plot(on_figure, **opts)


def test_1():
    import numpy as np
    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    scatter(x=x, y=y, z=z, c=c, cb_label='value')


if __name__ == '__main__':
    test_1()
