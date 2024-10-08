import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from zmlx.ui.GuiBuffer import gui

__Captions = [None]

Line = gl.GLLinePlotItem
Grid = gl.GLGridItem
Scatter = gl.GLScatterPlotItem
Mesh = gl.GLMeshItem


def apply(oper=None, caption=None, on_top=None):
    if caption is not None:
        __Captions[0] = caption
    if gui.exists() and oper is not None:
        gui.get_widget(the_type=gl.GLViewWidget, oper=oper, caption=__Captions[0], on_top=on_top,
                       icon='gpu.jpg')


def get_widget(caption=None, on_top=None):
    widgets = []
    apply(oper=lambda w: widgets.append(w), caption=caption, on_top=on_top)
    if len(widgets) > 0:
        return widgets[0]


def make_fn(name):
    def func(*args, caption=None, on_top=None, **kwargs):
        result = []

        def oper(widget):
            try:
                f = getattr(widget, name)
                r = f(*args, **kwargs)
                result.append(r)
            except Exception as err:
                print(err)

        apply(oper=oper, caption=caption, on_top=on_top)
        if len(result) > 0:
            return result[0]

    return func


reset = make_fn('reset')
add_item = make_fn('addItem')
remove_item = make_fn('removeItem')
clear = make_fn('clear')
orbit = make_fn('orbit')
pan = make_fn('pan')
set_background_color = make_fn('setBackgroundColor')


def set_option(key, value, **kwargs):
    """
    设置一个选项
    """

    def f(widget):
        widget.opts[key] = value
        widget.update()

    apply(oper=f, **kwargs)


def set_distance(dist, **kwargs):
    """
    设置距离
    """
    set_option('distance', dist, **kwargs)


def set_center(pos, **kwargs):
    """
    设置中心
    """
    set_option('center', pg.Vector(*pos), **kwargs)


def add_grid(x=-10, y=-10, z=-10, **kwargs):
    """
    添加网格
    """
    g = Grid()
    g.rotate(90, 0, 1, 0)
    g.translate(x, 0, 0)
    add_item(g, **kwargs)

    g = Grid()
    g.rotate(90, 1, 0, 0)
    g.translate(0, y, 0)
    add_item(g, **kwargs)

    g = Grid()
    g.translate(0, 0, z)
    add_item(g, **kwargs)


def add_box(left, right, line=None, caption=None, on_top=None, **kwargs):
    """
    添加一个立方体框
    """
    assert len(left) == 3 and len(right) == 3
    pos = []
    for i0, i1, i2 in [(0, 1, 2), (1, 2, 0), (2, 0, 1)]:
        for x in [left[i0], right[i0]]:
            for y in [left[i1], right[i1]]:
                p = [0, 0, 0]
                p[i0] = x
                p[i1] = y
                p[i2] = left[i2]
                pos.append(p)
                p = [0, 0, 0]
                p[i0] = x
                p[i1] = y
                p[i2] = right[i2]
                pos.append(p)
    if line is None:
        line = Line(pos=np.array(pos), mode='lines', **kwargs)
        add_item(line, caption=caption, on_top=on_top)
        return line
    else:
        line.setData(pos=np.array(pos), mode='lines', **kwargs)
        return line


if __name__ == '__main__':
    gui.execute(lambda: (add_box((0, 0, 0), (-5, -5, -5)),
                         add_grid(),
                         set_center([-2.5, -2.5, -2.5]),
                         set_distance(50),
                         ), close_after_done=False)
