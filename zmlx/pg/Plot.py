# -*- coding: utf-8 -*-


import pyqtgraph as pg
from zml import gui

__CaptionVal = [None, ]


def apply(oper=None, caption=None, on_top=None):
    if caption is not None:
        __CaptionVal[0] = caption
    if gui.exists() and oper is not None:
        gui.get_widget(type=pg.PlotWidget, oper=oper, caption=__CaptionVal[0], on_top=on_top)


def make_fn(name):
    def func(*args, caption=None, on_top=None, **kwargs):
        result = []
        apply(oper=lambda widget: result.append(getattr(widget, name)(*args, **kwargs)),
              caption=caption, on_top=on_top)
        if len(result) > 0:
            return result[0]
    return func


plot = make_fn('plot')
addItem = make_fn('addItem')
removeItem = make_fn('removeItem')
autoRange = make_fn('autoRange')
clear = make_fn('clear')
setAxisItems = make_fn('setAxisItems')
setXRange = make_fn('setXRange')
setYRange = make_fn('setYRange')
setRange = make_fn('setRange')
setAspectLocked = make_fn('setAspectLocked')
setLimits = make_fn('setLimits')
setLabel = make_fn('setLabel')
setMouseEnabled = make_fn('setMouseEnabled')
setXLink = make_fn('setXLink')
setYLink = make_fn('setYLink')
enableAutoRange = make_fn('enableAutoRange')
disableAutoRange = make_fn('disableAutoRange')
register = make_fn('register')
unregister = make_fn('unregister')
viewRect = make_fn('viewRect')
setLogMode = make_fn('setLogMode')
showGrid = make_fn('showGrid')
showAxis = make_fn('showAxis')

