# -*- coding: utf-8 -*-


import timeit

from zml import time2str, gui


class GuiIterator:
    """
    基于GUI界面的求解过程控制。自动调用模型的迭代和绘图，并确保绘图函数不会过于频繁地调用，保证计算效率；
    """

    def __init__(self, iterate, plot=None, info=None):
        """
        初始化：其中：
        iterate：程序内核进行计算迭代
        plot：绘图操作
        info：返回当前模型的状态信息
        """
        self.iterate = iterate
        self.plot = plot
        if info is None:
            self.info = self.time_info
        else:
            self.info = info
        self.time_iter = 0
        self.time_plot = 0
        self.step = 0
        self.ratio = 0.2
        self._ploterr_shown = False
        self._infoerr_shown = False

    def time_info(self):
        return f'总耗时{time2str(self.time_iter + self.time_plot)}. 其中内核耗时{time2str(self.time_iter)}, 界面绘图耗时{time2str(self.time_plot)}'

    def call(self, f):
        t_beg = timeit.default_timer()
        r = f()
        return timeit.default_timer() - t_beg, r

    def __call__(self, *args, **kwargs):
        assert self.iterate is not None
        # 迭代计算
        t, r = self.call(lambda: self.iterate(*args, **kwargs))
        self.step += 1
        self.time_iter += t
        if not gui.exists():
            return r
        gui.break_point()
        assert 0.0 < self.ratio < 0.5
        if self.time_plot < self.time_iter * self.ratio:
            if self.plot is not None:
                try:
                    self.time_plot += self.call(self.plot)[0]
                except Exception as err:
                    # 绘图时出现错误，则仅仅在第一次出现的时候显示出来
                    # 不去阻塞程序的运行
                    if not self._ploterr_shown:
                        print(f'{__file__}: {err}')
                        self._ploterr_shown = True
        if self.step % 10 == 0:
            if self.info is not None:
                try:
                    gui.status(self.info())
                except Exception as err:
                    # 状态信息的输出，也不会因为错误而阻塞程序运行
                    if not self._infoerr_shown:
                        print(f'{__file__}: {err}')
                        self._infoerr_shown = True
        return r
