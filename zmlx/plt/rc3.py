from zmlx.geometry import rect_3d as rect3
from zmlx.plt.cbar import add_cbar
from zmlx.plt.cmap import get_cm
from zmlx.plt.on_figure import add_axes3


def add_rc3(
        ax, rc3, *, face_color=None, face_alpha=None, face_cmap=None,
        edge_width=0.1,
        edge_color=(0, 0, 0, 0.3),
        cbar=None):
    """
    在指定的轴上绘制三维的矩形集合
    Args:
        ax: 需要绘图的轴
        rc3: 矩形集合，每个矩形用一个rect_3d对象表示
        face_color: 颜色值(数量等于rc3的数量)
        face_alpha: 透明度(数量等于rc3的数量)
        face_cmap: 颜色表
        edge_width: 线的宽度
        edge_color: 边的颜色
        cbar: 颜色条的参数，例如{'label': 'label', 'title': 'title'}

    Returns:
        Poly3DCollection
    """
    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    if face_color is None:  # 此时用颜色来代替序号
        face_color = list(range(len(rc3)))
    assert len(face_color) == len(rc3), \
        'The count of face_color must equal to the count of rc3'

    if face_alpha is None:  # 默认不透明
        face_alpha = 1.0

    face_cmap = get_cm(face_cmap)

    face_color = np.asarray(face_color)
    face_c_min, face_c_max = face_color.min(), face_color.max()
    norm = Normalize(vmin=face_c_min, vmax=face_c_max)
    rgba_colors = face_cmap(norm(face_color))

    if isinstance(face_alpha, (list, np.ndarray)):
        # 独立透明度
        rgba_colors[:, 3] = np.clip(face_alpha, 0.0, 1.0)
    else:
        rgba_colors[:, 3] = face_alpha

    # 生成面数据
    faces = [rect3.get_vertexes(item) for item in rc3]

    collection = Poly3DCollection(
        faces,
        facecolors=rgba_colors,
        edgecolors=edge_color,
        linewidths=edge_width
    )
    ax.add_collection3d(collection)

    if cbar is not None:
        add_cbar(ax, clim=(face_c_min, face_c_max), cmap=face_cmap, **cbar)

    return collection


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
             cbar=dict(label='Index', title='Index', shrink=0.5), )


if __name__ == '__main__':
    test()
