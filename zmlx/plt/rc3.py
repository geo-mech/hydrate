from zmlx.plt.on_axes.rc3 import add_rc3
from zmlx.plt.on_figure import add_axes3


def show_rc3(
        rc3, *, clabel=None, cbar=None, **opts):
    """
    绘制三维的矩形集合
    Args:
        rc3: 矩形集合，每个矩形用一个rect_3d对象表示
        clabel: 颜色条的标签
        cbar: 颜色条的参数，例如{'label': 'label', 'title': 'title'}
        **opts: 其它传递给plot的参数
    Returns:
        None
    """
    from zmlx.ui import plot
    if clabel is not None:
        if cbar is None:
            cbar = dict(label=clabel)
        else:
            cbar['label'] = clabel

    default_opts = dict(
        aspect='equal',
        tight_layout=True,
        xlabel='x',
        ylabel='y',
        zlabel='z',
    )
    opts = {
        **default_opts, **opts
    }
    plot(add_axes3, add_rc3, rc3, cbar=cbar, **opts)


def test():
    from zmlx.geometry.dfn_v3 import to_rc3, create_demo
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(5, 9))
        alpha.append(random.uniform(0, 1))
    show_rc3(rc3, gui_mode=True,
             cbar=dict(label='Index', title='Index', shrink=0.5),
             )


if __name__ == '__main__':
    test()
