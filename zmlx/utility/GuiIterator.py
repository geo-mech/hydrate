# -*- coding: utf-8 -*-


import timeit
from zml import time2str, gui
import warnings


class GuiIterator:
    """
    基于GUI界面的求解过程控制。自动调用模型的迭代和绘图，并确保绘图函数不会过于频繁地调用，保证计算效率；
    """

    def __init__(self, iterate, plot=None, info=None):
        """
        初始化：其中：
            iterate：程序内核进行计算迭代 (将接受__call__的所有参数)
            plot：绘图操作 (函数不接受任何参数)
            info：返回当前模型的状态信息 (函数不接受任何参数) 可以为None
        """
        assert hasattr(iterate, '__call__')
        self.iterate = iterate
        assert hasattr(plot, '__call__')
        self.plot = plot
        if info is None:
            self.info = self.time_info
        else:
            assert hasattr(info, '__call__')
            self.info = info
        self.time_iter = 0
        self.time_plot = 0
        self.step = 0
        self.ratio = 0.2

    def time_info(self):
        """
        返回程序的耗时情况
        """
        return f'总耗时{time2str(self.time_iter + self.time_plot)}. 其中内核耗时{time2str(self.time_iter)}, 界面绘图耗时{time2str(self.time_plot)}'

    @staticmethod
    def timing(f):
        """
        调用函数并计时
        """
        t_beg = timeit.default_timer()
        r = None if f is None else f()
        return timeit.default_timer() - t_beg, r

    def __call__(self, *args, **kwargs):
        """
        调用iterate，并可能自动调用绘图操作. 返回 iterate执行的结果.
        """
        assert self.iterate is not None
        t, r = GuiIterator.timing(lambda: self.iterate(*args, **kwargs))
        self.step += 1
        self.time_iter += t
        if not gui.exists():
            return r
        gui.break_point()
        assert 0.0 < self.ratio < 0.5
        if self.time_plot < self.time_iter * self.ratio:
            if self.plot is not None:
                try:
                    self.time_plot += GuiIterator.timing(self.plot)[0]
                except Exception as err:
                    warnings.warn(f'meet exception <{err}> when run <{self.plot}>')
        if self.step % 10 == 0:
            if self.info is not None:
                try:
                    gui.status(self.info())
                except Exception as err:
                    warnings.warn(f'meet exception <{err}> when run <{self.info}>')
        return r
