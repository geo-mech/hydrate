"""
显示三维矩形（主要用于显示dfn）. 其中一个三维矩形利用9个数字（矩形中心坐标和两个相邻边的中心坐标）来表示. 另外，对于任何一个矩形，都有颜色和
透明度两个通道.
"""

from zml import *
from zmlx.pg.plot3 import *
from zmlx.pg.get_color import get_color
from zmlx.alg.clamp import clamp
from zmlx.pg.colormap import coolwarm
import warnings


def center(x, y):
    """
    返回点x和y的中心点
    """
    return [(x[i] + y[i]) / 2 for i in range(3)]


def symmet(c, x):
    """
    返回x关于中心点x的对称点
    """
    return [c[i] * 2 - x[i] for i in range(3)]


def show_rc3(rc3, color=None, alpha=None, cmap=None, caption=None, on_top=None):
    """
    显示一组三维的离散裂缝网络
    """
    assert len(rc3) > 0

    vertexes = []
    faces = []

    for c0, c1, c2, a0, a1, a2, b0, b1, b2 in rc3:
        p0 = [c0, c1, c2]

        p1 = [a0, a1, a2]
        p2 = [b0, b1, b2]
        p3 = symmet(p0, p1)
        p4 = symmet(p0, p2)

        p5 = center(p1, p2)
        p6 = center(p2, p3)
        p7 = center(p3, p4)
        p8 = center(p4, p1)

        p1 = symmet(p5, p0)
        p2 = symmet(p6, p0)
        p3 = symmet(p7, p0)
        p4 = symmet(p8, p0)

        i0 = len(vertexes)

        vertexes.append(p1)
        vertexes.append(p2)
        vertexes.append(p3)
        vertexes.append(p4)

        faces.append([i0, i0 + 1, i0 + 2])
        faces.append([i0, i0 + 2, i0 + 3])

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
    else:
        widget.mesh_1 = Mesh(vertexes=vertexes, faces=faces, faceColors=colors,
                             smooth=False)
        widget.mesh_1.setGLOptions('opaque')
        add_item(widget.mesh_1)
        set_distance(get_distance([x_min, y_min, z_min], [x_max, y_max, z_max]))
        set_center(center([x_min, y_min, z_min], [x_max, y_max, z_max]))

    if hasattr(widget, 'line_1'):
        add_box([x_min, y_min, z_min], [x_max, y_max, z_max],
                line=widget.line_1)
    else:
        widget.line_1 = add_box([x_min, y_min, z_min],
                                [x_max, y_max, z_max])



