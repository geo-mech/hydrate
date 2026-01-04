import warnings

from zmlx.geometry import rect_3d as rect3
from zmlx.plt.cmap import get_cm
from zmlx.plt.on_axes.cbar import add_cbar


def add_rc3(
        ax, rc3, *, face_color=None, face_alpha=None, face_cmap=None,
        edge_width=0.1,
        edge_color=(0, 0, 0, 0.3),
        edge_only=False,
        cbar=None, **deprecated_opts):
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
        edge_only: 是否只绘制边界（此参数为True的时候，所有的面都将是完全透明的）
        cbar: 颜色条的参数，例如{'label': 'label', 'title': 'title'}

    Returns:
        Poly3DCollection
    """
    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    if 'color' in deprecated_opts:
        if face_color is None:
            face_color = deprecated_opts['color']
        else:
            warnings.warn(f'Option <color> is deprecated (remove after 2026-12-9), use <face_color> instead',
                          DeprecationWarning, stacklevel=2)

    if 'alpha' in deprecated_opts:
        if face_alpha is None:
            face_alpha = deprecated_opts['alpha']
        else:
            warnings.warn(f'Option <alpha> is deprecated (remove after 2026-12-9), use <face_alpha> instead',
                          DeprecationWarning, stacklevel=2)

    if 'cmap' in deprecated_opts:
        if face_cmap is None:
            face_cmap = deprecated_opts['cmap']
        else:
            warnings.warn(f'Option <cmap> is deprecated (remove after 2026-12-9), use <face_cmap> instead',
                          DeprecationWarning, stacklevel=2)

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

    if edge_only:
        face_alpha = 0.0

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
