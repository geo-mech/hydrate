import timeit
import warnings

from zmlx.alg.clamp import clamp
from zmlx.alg.time2str import time2str
from zmlx.ui import gui


class GuiIterator:
    """
    基于GUI界面的求解过程控制。自动调用模型的迭代和绘图，并确保绘图函数不会过于频繁地调用，保证计算效率；
    """

    def __init__(self, iterate=None, plot=None, info=None, ratio=None):
        """
        初始化：其中：
            iterate: 程序内核进行计算迭代 (将接受__call__的所有参数)
            plot: 绘图操作 (函数不接受任何参数)
            info: 返回当前模型的状态信息 (函数不接受任何参数) 可以为None
            ratio: gui绘图所占据的总的时长的比例。默认为0.2
        """
        if callable(iterate):
            self.iterate = iterate
        else:
            self.iterate = None

        if callable(plot):
            self.plot = plot
        else:
            self.plot = None

        if callable(info):
            self.info = info
        else:
            self.info = self.time_info

        self.time_iter = 0
        self.time_plot = 0
        self.step = 0
        self.ratio = 0.2 if ratio is None else clamp(ratio, 1.0e-3, 0.3)

    def time_info(self):
        """
        返回程序的耗时情况
        """
        return (f'Time. All = {time2str(self.time_iter + self.time_plot)}. '
                f'Iter = {time2str(self.time_iter)}, '
                f'Plot = {time2str(self.time_plot)}')

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
        if self.iterate is None:  # 此时不需要迭代
            return

        assert self.iterate is not None
        t, r = GuiIterator.timing(lambda: self.iterate(*args, **kwargs))
        self.step += 1
        self.time_iter += t

        if not gui.exists():
            return r

        gui.break_point()
        assert 0.0 <= self.ratio < 0.5, f'The GuiIterator.ratio should be in [0, 0.5), but get {self.ratio}'

        if self.time_plot < self.time_iter * self.ratio and self.plot is not None:
            try:
                self.time_plot += GuiIterator.timing(self.plot)[0]
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <{self.plot}>')
        if self.step % 10 == 0 and self.info is not None:
            try:
                gui.status(self.info())
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <{self.info}>')
        return r
