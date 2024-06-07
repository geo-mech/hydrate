import pyqtgraph as pg

from zmlx.ui.GuiBuffer import gui

__CaptionVal = [None, ]


def apply(oper=None, caption=None, on_top=None):
    if caption is not None:
        __CaptionVal[0] = caption
    if gui.exists() and oper is not None:
        gui.get_widget(type=pg.PlotWidget, oper=oper, caption=__CaptionVal[0], on_top=on_top,
                       icon='gpu.jpg')


def make_fn(name):
    def func(*args, caption=None, on_top=None, **kwargs):
        result = []
        apply(oper=lambda widget: result.append(getattr(widget, name)(*args, **kwargs)),
              caption=caption, on_top=on_top)
        if len(result) > 0:
            return result[0]

    return func


plot = make_fn('plot')
add_item = make_fn('addItem')
remove_item = make_fn('removeItem')
auto_range = make_fn('autoRange')
clear = make_fn('clear')
set_axis_items = make_fn('setAxisItems')
set_x_range = make_fn('setXRange')
set_y_range = make_fn('setYRange')
set_range = make_fn('setRange')
set_aspect_locked = make_fn('setAspectLocked')
set_limits = make_fn('setLimits')
set_label = make_fn('setLabel')
set_mouse_enabled = make_fn('setMouseEnabled')
set_x_link = make_fn('setXLink')
set_y_link = make_fn('setYLink')
enable_auto_range = make_fn('enableAutoRange')
disable_auto_range = make_fn('disableAutoRange')
register = make_fn('register')
unregister = make_fn('unregister')
view_rect = make_fn('viewRect')
set_log_mode = make_fn('setLogMode')
show_grid = make_fn('showGrid')
show_axis = make_fn('showAxis')
