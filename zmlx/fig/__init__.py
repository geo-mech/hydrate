"""
定义数据驱动的绘图模式.
"""
from zmlx.fig.data import save, load
from zmlx.plt.on_axes.data import *
from zmlx.plt.on_axes.data import add_to_axes
from zmlx.plt.on_figure.data import *
from zmlx.plt.on_figure.data import add_to_figure, show, show as plt_show

_keep = [add_to_axes, add_to_figure, show, plt_show, subplot, surface
         ]
