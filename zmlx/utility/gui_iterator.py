import timeit

import zmlx.alg.sys as warnings
from zmlx.alg.base import time2str, clamp
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
        self.history = []
        self.max_history_shown = 1000  # 在绘图显示迭代耗时的时候，最多显示的记录的个数.

    def time_info(self):
        """
        返回程序的耗时情况
        """
        return (f'Time. All = {time2str(self.time_iter + self.time_plot)}. '
                f'Iter = {time2str(self.time_iter)}, '
                f'Plot = {time2str(self.time_plot)}')

    def _show_timing(self, figure):
        """
        在Matplotlib的Figure上显示history。采用双y的坐标系，其中x为step，左侧的y为迭代的耗时，右侧的y为绘图的耗时.
        注意：如果self.history的长度小于2，则不需要绘图.
        Args:
            figure: Matplotlib的Figure对象
        Returns:
            None
        """
        figure.suptitle(self.time_info())
        if len(self.history) < 2 or self.max_history_shown < 10:
            return
        history = self.history[-self.max_history_shown:]
        step = [h[0] for h in history]
        t_iter = [h[1] for h in history]
        step_plot = [h[0] for h in history if h[2] > 0]
        t_plot = [h[2] for h in history if h[2] > 0]

        ax1 = figure.add_subplot(111)
        line1, = ax1.plot(step, t_iter, '#4A90A4', label='Iter Time')
        ax1.set_xlabel('Step')
        ax1.set_ylabel('Iter Time (s)', color='#4A90A4')
        ax1.tick_params(axis='y', labelcolor='#4A90A4')
        ax1.set_ylim(bottom=0)

        ax2 = ax1.twinx()
        line2, = ax2.plot(step_plot, t_plot, marker='o', linestyle='none', color='#C76464', label='Plot Time')
        ax2.set_ylabel('Plot Time (s)', color='#C76464')
        ax2.tick_params(axis='y', labelcolor='#C76464')
        ax2.set_ylim(bottom=0)
        figure.tight_layout()

    def plot_timing(self):
        """
        绘图显示迭代耗时的历史记录
        """
        if self.max_history_shown >= 10:
            from zmlx.ui import plot as do_plot
            do_plot(lambda fig: self._show_timing(fig),
                    caption='迭代耗时', on_top=False
                    )

    @staticmethod
    def timing(f):
        """
        调用函数并计时
        """
        t_beg = timeit.default_timer()
        r = None if f is None else f()
        return timeit.default_timer() - t_beg, r

    def __call__(self, *args, forced_plot=False, **kwargs):
        """
        调用iterate，并可能自动调用绘图操作. 返回 iterate执行的结果.
        Args:
            *args: 迭代函数的参数
            forced_plot: 是否强制绘图
            **kwargs: 迭代函数的参数参数
        """
        if self.iterate is None:  # 此时不需要迭代
            return None

        def f():  # 不带参数的内核函数
            assert callable(self.iterate), 'The iterate function should be callable.'
            return self.iterate(*args, **kwargs)

        t1, r = GuiIterator.timing(f)
        t2 = 0.0
        self.step += 1
        self.time_iter += t1

        if len(self.history) > 100000:  # 限制历史记录的长度
            self.history = self.history[-50000:]

        if not gui.exists():
            self.history.append((self.step, t1, t2))
            return r

        gui.break_point()
        assert 0.0 <= self.ratio < 0.5, f'The GuiIterator.ratio should be in [0, 0.5), but get {self.ratio}'

        if (self.time_plot < self.time_iter * self.ratio and self.plot is not None) or forced_plot:
            try:
                t2 = GuiIterator.timing(self.plot_all)[0]
                self.time_plot += t2
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <GuiIterator.plot_all>')

        self.history.append((self.step, t1, t2))
        if self.step % 10 == 0 and self.info is not None:
            try:
                gui.status(self.info())
            except Exception as err:
                warnings.warn(f'meet exception <{err}> when run <GuiIterator.info>')

        return r

    def plot_all(self):
        """
        执行所有的绘图，包括外部的绘图和耗时的绘图
        """
        if callable(self.plot):
            self.plot()
        self.plot_timing()
