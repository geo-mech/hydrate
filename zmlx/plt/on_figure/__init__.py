"""
在这个文件中，处理和figure相关的方法. 这里，不直接处理在Axes上的操作。这里，主要是首先常见Axes，然后，再
基于on_axes中定义的方法，来创建具体的图形。
"""
from typing import Optional

from zmlx.plt.on_figure._img import add_axes_img
from zmlx.plt.on_figure._layout import calc_best_layout, calculate_subplot_layout
from zmlx.plt.on_figure._subplot import add_subplot, add_axes2, add_axes3, plot_on_figure, plot_on_axes


class AutoLayout:
    def __init__(self, figure, num_plots: int, subplot_aspect_ratio: Optional[float] = None, **other_opts):
        self.figure = figure
        self.index = 0
        self.num_plots = num_plots
        self.nrows, self.ncols = calc_best_layout(
            figure, num_plots, subplot_aspect_ratio=subplot_aspect_ratio)
        self.other_opts = other_opts

    def _opts(self, kwargs):
        self.index += 1
        assert self.index <= self.num_plots, f"index {self.index} is out of range, max index is {self.num_plots}"
        res = kwargs.copy()
        res['nrows'] = self.nrows
        res['ncols'] = self.ncols
        res['index'] = self.index
        for k, v in self.other_opts.items():
            res.setdefault(k, v)
        return res

    def add_subplot(self, *args, **kwargs):
        return add_subplot(self.figure, *args, **self._opts(kwargs))

    def add_axes2(self, *args, **kwargs):
        return add_axes2(self.figure, *args, **self._opts(kwargs))

    def add_axes3(self, *args, **kwargs):
        return add_axes3(self.figure, *args, **self._opts(kwargs))
