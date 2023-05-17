# -*- coding: utf-8 -*-


from zmlx.pg.GLItem import *
from zml import gui
import pyqtgraph.opengl as gl
import pyqtgraph as pg
import numpy as np


__Captions = [None]


def apply(oper=None, caption=None, on_top=None):
    if caption is not None:
        __Captions[0] = caption
    if gui.exists() and oper is not None:
        gui.get_widget(type=gl.GLViewWidget, oper=oper, caption=__Captions[0], on_top=on_top)


def make_fn(name):
    def func(*args, caption=None, on_top=None, **kwargs):
        result = []
        apply(oper=lambda widget: result.append(getattr(widget, name)(*args, **kwargs)),
              caption=caption, on_top=on_top)
        if len(result) > 0:
            return result[0]
    return func


reset = make_fn('reset')
addItem = make_fn('addItem')
removeItem = make_fn('removeItem')
clear = make_fn('clear')
orbit = make_fn('orbit')
pan = make_fn('pan')
setBackgroundColor = make_fn('setBackgroundColor')


def _setOpt(key, value, **kwargs):
    def f(widget):
        widget.opts[key] = value
        widget.update()

    apply(oper=f, **kwargs)


def setDistance(dist, **kwargs):
    _setOpt('distance', dist, **kwargs)


def setCenter(pos, **kwargs):
    _setOpt('center', pg.Vector(*pos), **kwargs)


def addGrid(*args, **kwargs):
    g = Grid()
    g.rotate(90, 0, 1, 0)
    g.translate(-10, 0, 0)
    addItem(g, *args, **kwargs)

    g = Grid()
    g.rotate(90, 1, 0, 0)
    g.translate(0, -10, 0)
    addItem(g, *args, **kwargs)

    g = Grid()
    g.translate(0, 0, -10)
    addItem(g, *args, **kwargs)


def addBox(left, right, caption=None, on_top=None, **kwargs):
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
    line = Line(pos=np.array(pos), mode='lines', **kwargs)
    addItem(line, caption=caption, on_top=on_top)


if __name__ == '__main__':
    def f():
        addBox((0, 0, 0), (-5, -5, -5))
        addGrid()
        setDistance(50)
    gui.execute(f, close_after_done=False)
