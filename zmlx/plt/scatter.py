def scatter(
        items=None, get_val=None, x=None, y=None, z=None, c=None, get_pos=None, cb_label=None, **opts):
    """
    绘制三维的散点图
    """
    from zmlx.plt.on_axes.data import scatter
    from zmlx.plt.on_axes import plot3d
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

    plot3d(scatter(x, y, z, c=c, cbar=dict(label=cb_label)))


def test():
    import numpy as np
    from zmlx.plt.on_axes.data import scatter
    from zmlx.plt.on_axes import plot3d

    x = np.random.rand(100)
    y = np.random.rand(100)
    z = np.random.rand(100)
    c = np.random.rand(100)
    plot3d(
        scatter(x, y, z, c=c, cbar=dict(label='label', title='title')),
        title='My Scatter Plot',
        xlabel='x/m', gui_mode=True, clear=True, caption='MyTest'
    )


if __name__ == '__main__':
    test()
