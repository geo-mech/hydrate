try:
    import numpy as np
except Exception as e:
    print(e)
    np = None

from zmlx.plt.cmap import get_cm
from zmlx.plt.on_axes import plot_on_axes


def plot_trisurf(x=None, y=None, z=None,
                 cmap='coolwarm',
                 **kwargs):
    """
    绘制三维三角化曲面图，支持坐标轴标签和颜色映射配置

    Parameters
    ----------
    x, y, z : array-like, 1D
        数据点的三维坐标数组，必须为相同长度的一维数组
    cmap : str or Colormap, default 'coolwarm'
        曲面颜色映射，支持所有Matplotlib注册的colormap名称
    **kwargs : dict
        传递给底层plot_on_axes函数的附加参数
    """

    def on_axes(ax):
        res = ax.plot_trisurf(x, y, z, cmap=cmap, antialiased=True)
        ax.get_figure().colorbar(res, ax=ax)

    plot_on_axes(on_axes, dim=3, **kwargs)


def scatter(items=None, get_val=None, x=None, y=None, z=None, c=None,
            get_pos=None,
            alpha=1.0,
            cb_label=None,
            cmap='coolwarm',
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

    def on_axes(ax):
        obj = ax.scatter(x, y, z, c=c, cmap=cmap, alpha=alpha)
        cbar = ax.get_figure().colorbar(obj, ax=ax)
        if cb_label is not None:
            cbar.set_label(cb_label)

    plot_on_axes(on_axes, dim=3, **opts)


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
    from zmlx.geometry import rect_3d as rect3
    from matplotlib.colors import Normalize
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
