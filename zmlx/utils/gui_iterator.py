"""GUI 求解过程迭代控制器。

自动调用模型迭代与绘图，通过计时统计自适应控制绘图频率，
确保绘图耗时不超过迭代总时间的设定比例。
同时提供 ``get_gui_iter`` 函数用于获取全局单例。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
import timeit


from zmlx.algs.base import time2str, clamp
from zmlx.ui import gui
from zmlx.system import is_headless


class GuiIterator:
    """基于 GUI 的求解过程自适应控制器。

    自动调用模型的迭代（``iterate``）和绘图（``plot``），
    通过时间统计控制绘图频率，确保绘图耗时不超过设定的比例。
    支持 GUI 和无 GUI 模式自动切换。
    """

    def __init__(
        self,
        iterate=None,
        plot=None,
        info=None,
        ratio=None,
        figure_caption=None,
        max_plot_interval=None,
        gui_only=None,
    ):
        """初始化迭代控制器。

        Args:
            iterate: 迭代回调函数（接收 ``*args, **kwargs``）。
            plot: 绘图回调函数（无参数）。
            info: **【已不再使用】** 状态信息回调（无参数，返回字符串）。
                  它原先每 10 步把 ``time_info()`` 送到状态栏，现在改由「GUI 迭代器」
                  控件显示；本参数保留只为兼容旧调用。
            ratio: 绘图耗时占总耗时的最大比例，默认 0.2，
                   钳制在 ``[1e-3, 0.3]``。
            figure_caption: 耗时绘图窗口的标题。
            max_plot_interval: 最大绘图间隔（step 数），
                               超过此间隔强制绘图。None 时不限制。
            gui_only: 是否仅在 GUI 模式下绘图。
                      None 时由 ``is_headless()`` 自动决定。
        """
        self._iterate = iterate if callable(iterate) else None
        self._plot = plot if callable(plot) else None
        # ⚠️ ``info`` 保留在签名里只为兼容（本项目的公开 API 只增不改），
        #    **已经不再被调用**：它原先的作用是每 10 步把 ``time_info()`` 送到状态栏；
        #    现在那件事由「GUI 迭代器」控件（``GuiIteratorEdit``）承担 —— 用专门的
        #    控件显示比挤在状态栏里清楚得多（而且原来那条不带 timeout，会长期占着
        #    状态栏，把别的内容都顶掉）。
        self.info = info if callable(info) else self.time_info

        self._step_last_plot = None  # 最后一次绘图的时候的step
        self._time_iter = 0
        self._time_plot = 0
        self._step = 0
        self._ratio = 0.2 if ratio is None else clamp(ratio, 1.0e-3, 0.3)
        self._history = []
        self._max_history_shown = 1000  # 在绘图显示迭代耗时的时候，最多显示的记录的个数.
        self.figure_caption = figure_caption  # 耗时绘图的Caption
        self.max_plot_interval = max_plot_interval  # 最大绘图间隔，单位为step
        self.gui_only = (
            not is_headless() if gui_only is None else bool(gui_only)
        )  # 是否只在gui模式下绘图(如果gui不存在，则永远不会执行绘图)

    def time_info(self):
        """返回程序的耗时情况。

        Returns:
            str: 累计总耗时、迭代耗时和绘图耗时的格式化字符串。
        """
        return (
            f"Time. All = {time2str(self._time_iter + self._time_plot)}. "
            f"Iter = {time2str(self._time_iter)}, "
            f"Plot = {time2str(self._time_plot)}"
        )

    @property
    def iterate(self):
        """迭代回调函数（可读/写）。设置为 None 或不可调用对象时引发 TypeError。"""
        return self._iterate

    @iterate.setter
    def iterate(self, value):
        if value is not None and not callable(value):
            raise TypeError(f'iterate must be callable or None, got {type(value).__name__}')
        self._iterate = value
        self._time_iter = 0
        self._time_plot = 0

    @property
    def plot(self):
        """绘图回调函数（可读/写）。设置为 None 或不可调用对象时引发 TypeError。"""
        return self._plot

    @plot.setter
    def plot(self, value):
        if value is not None and not callable(value):
            raise TypeError(f'plot must be callable or None, got {type(value).__name__}')
        self._plot = value
        self._time_iter = 0
        self._time_plot = 0

    @property
    def ratio(self):
        """绘图时间比例（可读/写）。取值钳制在 ``[1e-3, 0.3]``。"""
        return self._ratio

    @ratio.setter
    def ratio(self, value):
        self._ratio = clamp(value, 1.0e-3, 0.3)
        self._time_iter = 0
        self._time_plot = 0

    def show_timing(self, figure):
        """
        在Matplotlib的Figure上显示history。采用双y的坐标系，其中x为step，左侧的y为迭代的耗时，右侧的y为绘图的耗时.
        注意：如果self._history的长度小于2，则不需要绘图.
        Args:
            figure: Matplotlib的Figure对象
        Returns:
            None
        """
        figure.clear()
        figure.suptitle(self.time_info())
        if len(self._history) < 2 or self._max_history_shown < 10:
            return
        history = self._history[-self._max_history_shown :]
        step = [h[0] for h in history]
        t_iter = [h[1] for h in history]
        step_plot = [h[0] for h in history if h[2] > 0]
        t_plot = [h[2] for h in history if h[2] > 0]

        ax1 = figure.add_subplot(111)
        (line1,) = ax1.plot(step, t_iter, "#4A90A4", label="Iter Time")
        ax1.set_xlabel("Step")
        ax1.set_ylabel("Iter Time (s)", color="#4A90A4")
        ax1.tick_params(axis="y", labelcolor="#4A90A4")
        ax1.set_ylim(bottom=0)

        ax2 = ax1.twinx()
        (line2,) = ax2.plot(
            step_plot,
            t_plot,
            marker="o",
            linestyle="none",
            color="#C76464",
            label="Plot Time",
        )
        ax2.set_ylabel("Plot Time (s)", color="#C76464")
        ax2.tick_params(axis="y", labelcolor="#C76464")
        ax2.set_ylim(bottom=0)
        figure.tight_layout()

    def _plot_timing(self):
        """
        绘图显示迭代耗时的历史记录
        """
        if gui.exists():
            from zmlx.ui.tabs.gui_iter_edit import GuiIteratorEdit
            gui.get_widget(
                the_type=GuiIteratorEdit, caption='迭代器',
                on_top=False, oper=lambda w: w.set_data(self)
            )
        else:
            if self._max_history_shown >= 10 and not self.gui_only:
                from zmlx.ui import plot
                if isinstance(self.figure_caption, str):
                    caption = self.figure_caption
                else:
                    caption = "迭代耗时"
                plot(self.show_timing, caption=caption, on_top=False)

    @staticmethod
    def _timing(f):
        """
        调用函数并计时
        """
        t_beg = timeit.default_timer()
        r = None if f is None else f()
        return timeit.default_timer() - t_beg, r

    def __call__(self, *args, forced_plot=False, **kwargs):
        """调用迭代函数，并按需自动执行绘图。

        Args:
            *args: 传递给 ``iterate`` 的位置参数。
            forced_plot: 是否强制执行绘图（首次调用时自动为 True）。
            **kwargs: 传递给 ``iterate`` 的关键词参数。

        Returns:
            任意 | None: ``iterate`` 的执行结果（``iterate`` 为 None 时返回 None）。
        """
        if self.iterate is None:  # 此时不需要迭代
            return None

        def f():  # 不带参数的内核函数
            assert callable(self.iterate), "The iterate function should be callable."
            return self.iterate(*args, **kwargs)

        t1, r = GuiIterator._timing(f)
        t2 = 0.0
        self._step+= 1  # 迭代的步数增加
        self._time_iter += t1

        if len(self._history) > 100000:  # 限制历史记录的长度
            self._history = self._history[-50000:]

        if not gui.exists() and self.gui_only:
            self._history.append((self._step, t1, t2))
            return r

        if gui.exists():
            gui.break_point()
        assert 0.0 <= self.ratio < 0.5, (
            f"The GuiIterator.ratio should be in [0, 0.5), but get {self.ratio}"
        )

        if self._step_last_plot is None:
            forced_plot = True  # 确保执行一次绘图
        else:
            if self.max_plot_interval is not None:
                if self._step- self._step_last_plot > self.max_plot_interval:
                    forced_plot = True  # 距离上次绘图已经过于久远了，因此强制绘图

        if (
            self._time_plot < self._time_iter * self.ratio and self.plot is not None
        ) or forced_plot:
            try:
                t2 = GuiIterator._timing(self.plot_all)[0]
                self._time_plot += t2
            except Exception as err:
                warn(f"meet exception <{err}> when run <GuiIterator.plot_all>")

        self._history.append((self._step, t1, t2))

        return r

    def plot_all(self):
        """执行所有的绘图操作（外部绘图 + 耗时计时绘图）。

        仅在 GUI 存在或 ``gui_only`` 为 False 时执行。
        """
        if self.gui_only and not gui.exists():
            return
        if callable(self.plot):
            self.plot()
        self._plot_timing()
        # 更新最后一次绘图的时候的step
        self._step_last_plot = self._step



_gui_iter = None


def get_gui_iter(
    iterate=None,
    plot=None,
    info=None,
    ratio=None,
    figure_caption=None,
    max_plot_interval=None,
    gui_only=None,
):
    """获取全局唯一的 GuiIterator 实例.

    首次调用时创建新实例；后续调用返回同一个对象。
    传入的参数会更新到现有实例（None 表示不修改）。

    Args:
        iterate: 程序内核进行计算迭代 (将接受 __call__ 的所有参数)
        plot: 绘图操作 (函数不接受任何参数)
        info: **【已不再使用】** 状态信息回调（保留只为兼容旧调用）
        ratio: gui 绘图所占据的总的时长的比例，默认 0.2
        figure_caption: 耗时绘图的标题
        max_plot_interval: 最大绘图间隔 (step 数)
        gui_only: 是否只在 gui 模式下绘图

    Returns:
        GuiIterator: 全局唯一的迭代控制器。
    """
    global _gui_iter
    if _gui_iter is None:
        _gui_iter = GuiIterator(
            iterate=iterate,
            plot=plot,
            info=info,
            ratio=ratio,
            figure_caption=figure_caption,
            max_plot_interval=max_plot_interval,
            gui_only=gui_only,
        )
    else:
        # 更新已有的实例（仅更新非 None 的参数）
        params = {
            'iterate': iterate, 'plot': plot, 'info': info,
            'ratio': ratio, 'figure_caption': figure_caption,
            'max_plot_interval': max_plot_interval, 'gui_only': gui_only,
        }
        for key, value in params.items():
            if value is not None:
                setattr(_gui_iter, key, value)
    return _gui_iter