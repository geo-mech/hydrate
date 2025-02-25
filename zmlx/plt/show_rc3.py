import numpy as np

from zmlx.geometry import rect_3d as rect3
from zmlx.plt.plot_on_axes import plot_on_axes
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from zmlx.plt.get_cm import get_cm


def show_rc3(rc3, *, face_color=None, face_alpha=None, face_cmap=None,
             edge_width=0.1,
             edge_color=(0, 0, 0, 0.3),
             clabel=None,
             **opts):
    """
    绘制三维的矩形集合
    Args:
        rc3: 矩形集合，每个矩形用一个rect_3d对象表示
        face_color: 颜色值
        face_alpha: 透明度
        face_cmap: 颜色表
        edge_width: 线的宽度
        edge_color: 边的颜色
        clabel: 颜色条的标签
        **opts: 其它传递给plot_on_axes的参数
    Returns:
        None
    """
    if face_color is None:  # 此时用颜色来代替序号
        face_color = list(range(len(rc3)))
    assert len(face_color) == len(rc3), \
        'The count of face_color must equal to the count of rc3'

    if face_alpha is None:  # 默认不透明
        face_alpha = 1.0

    if face_cmap is None or isinstance(face_cmap, str):
        face_cmap = get_cm(face_cmap)

    face_color = np.asarray(face_color)
    norm = Normalize(vmin=face_color.min(), vmax=face_color.max())
    rgba_colors = face_cmap(norm(face_color))
    if isinstance(face_alpha, (list, np.ndarray)):
        rgba_colors[:, 3] = np.clip(face_alpha, 0, 1)  # 独立透明度
    else:
        rgba_colors[:, 3] = face_alpha

    def on_axes(ax):
        """
        在指定的轴上绘制面数据
        Args:
            ax: 需要绘图的轴

        Returns:
            None

        """
        from matplotlib.cm import ScalarMappable

        # 生成面数据
        faces = [rect3.get_vertexes(item) for item in rc3]

        collection = Poly3DCollection(
            faces,
            facecolors=rgba_colors,
            edgecolors=edge_color,
            linewidths=edge_width
        )
        ax.add_collection3d(collection)

        # 显式创建ScalarMappable对象
        mappable = ScalarMappable(norm=norm, cmap=face_cmap)
        mappable.set_array(face_color)
        cbar = ax.get_figure().colorbar(mappable, ax=ax)
        if clabel is not None:
            cbar.set_label(clabel)

    opts.setdefault('aspect', 'equal')
    plot_on_axes(on_axes, dim=3, **opts)


def test():
    from zmlx.geometry.dfn_v3 import to_rc3, create_demo
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(5, 9))
        alpha.append(random.uniform(0, 1))
    show_rc3(rc3, gui_mode=True)


if __name__ == '__main__':
    test()
