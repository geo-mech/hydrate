""" rc3 绘图工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.geometries import rect_3d as rect3
from zmlx.plt.cmap import get_cm
from zmlx.plt.on_axes._cbar import add_cbar


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

    # 旧参数 color/alpha/cmap 的兼容：只要调用方还在用旧名字就发告警；新参数优先。
    # ⚠️ 2026-10-21 前的写法恰好在"只有旧参数"时**不告警**、在"新旧都给"时才告警，
    #    等于旧用法从来没有被统计到（zmlx.system.warn 的 tag 也因此查不出来）。
    _old_to_new = dict(color='face_color', alpha='face_alpha', cmap='face_cmap')
    for old in _old_to_new:
        if old in deprecated_opts:
            warn(
                f'add_rc3 的参数 <{old}> 已弃用（remove after 2026-12-9）：'
                f'请改用 <{_old_to_new[old]}>；旧名字只在新名字未给时生效',
                DeprecationWarning, stacklevel=2, tag=f'add_rc3.{old}')

    if face_color is None and 'color' in deprecated_opts:
        face_color = deprecated_opts['color']
    if face_alpha is None and 'alpha' in deprecated_opts:
        face_alpha = deprecated_opts['alpha']
    if face_cmap is None and 'cmap' in deprecated_opts:
        face_cmap = deprecated_opts['cmap']

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
