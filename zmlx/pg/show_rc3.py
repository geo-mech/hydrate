"""
显示三维矩形（主要用于显示dfn）. 其中一个三维矩形利用9个数字（矩形中心坐标和两个相邻边的中心坐标）来表示. 另外，对于任何一个矩形，都有颜色和
透明度两个通道.
"""

from zml import *
from zmlx.alg.clamp import clamp
from zmlx.geometry import rect_3d as rect3
from zmlx.pg.plot3 import *
from zmlx.pg.get_color import get_color
from zmlx.pg.colormap import coolwarm
import warnings


def show_rc3(rc3, color=None, alpha=None, cmap=None, caption=None, on_top=None,
             reset_dist=True, reset_cent=True, gl_option=None):
    """
    显示一组三维的离散裂缝网络
        gl_option:  opaque, translucent, additive
    """
    if not gui.exists():
        return

    if len(rc3) <= 0:
        return

    vertexes = []
    faces = []

    for data in rc3:
        i0 = len(vertexes)
        faces.append([i0, i0 + 1, i0 + 2])
        faces.append([i0, i0 + 2, i0 + 3])
        for vtx in rect3.get_vertexes(data):
            vertexes.append(vtx)

    vertexes = np.array(vertexes)
    faces = np.array(faces)

    if color is None:
        color = 1

    if alpha is None:
        alpha = 1

    def get(t, i):
        if is_array(t):
            return t[i]
        else:
            return t if t is not None else 1

    def get_a(i):
        return get(alpha, i)

    def get_c(i):
        return get(color, i)

    def get_r(func, count):
        assert count > 0
        lr = func(0)
        rr = lr
        for i in range(1, count):
            v = func(i)
            lr = min(lr, v)
            rr = max(rr, v)
        return lr, rr

    # 颜色的范围
    cl, cr = get_r(get_c, len(rc3))
    if cl + 1.0e-10 >= cr:
        cl = cr - 1.0

    # 透明度的范围
    al, ar = get_r(get_a, len(rc3))
    if al + 1.0e-10 >= ar:
        al = ar - 1.0

    if cmap is None:
        cmap = coolwarm()

    colors = []
    for i in range(len(rc3)):
        c1 = get_color(cmap, cl, cr, get_c(i))
        assert len(c1) >= 3
        a1 = get_a(i)
        a1 -= al
        a1 /= max(1.0e-6, ar - al)
        a1 = clamp(a1, 0, 1)
        c2 = [c1[0], c1[1], c1[2], a1]
        colors.append(c2)
        colors.append(c2)  # 矩形分成了两个三角形来绘图

    colors = np.array(colors)

    x_min = np.min(vertexes[:, 0])
    x_max = np.max(vertexes[:, 0])

    y_min = np.min(vertexes[:, 1])
    y_max = np.max(vertexes[:, 1])

    z_min = np.min(vertexes[:, 2])
    z_max = np.max(vertexes[:, 2])

    widget = get_widget(caption=caption, on_top=on_top)
    if widget is None:
        warnings.warn(f'The widget is None. caption = {caption}, on_top = {on_top}')
        return

    if hasattr(widget, 'mesh_1'):
        widget.mesh_1.setMeshData(vertexes=vertexes, faces=faces, faceColors=colors,
                                  smooth=False)
        if reset_dist:
            set_distance(get_distance([x_min, y_min, z_min], [x_max, y_max, z_max]))
        if reset_cent:
            set_center([(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2])
    else:
        widget.mesh_1 = Mesh(vertexes=vertexes, faces=faces, faceColors=colors,
                             smooth=False)
        widget.mesh_1.setGLOptions('opaque' if gl_option is None else gl_option)
        add_item(widget.mesh_1)
        set_distance(get_distance([x_min, y_min, z_min], [x_max, y_max, z_max]))
        set_center([(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2])

    if hasattr(widget, 'line_1'):
        add_box([x_min, y_min, z_min], [x_max, y_max, z_max],
                line=widget.line_1)
    else:
        widget.line_1 = add_box([x_min, y_min, z_min],
                                [x_max, y_max, z_max])


def test():
    from zmlx.alg.dfn_v3 import to_rc3, create_demo
    import random
    rc3 = to_rc3(create_demo())
    color = []
    alpha = []
    for _ in rc3:
        color.append(random.uniform(0, 1))
        alpha.append(random.uniform(0, 1) ** 3)
    show_rc3(rc3, color=color, alpha=alpha, caption='dfn_v3')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
