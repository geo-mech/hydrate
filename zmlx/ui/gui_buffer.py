"""
zmlx GUI 执行框架。

== 核心用法 ==

所有 gui.xxx() 函数（break_point、progress、show_attrs 等）只有在通过
gui.execute() 启动主程序时才会生效。在非 GUI 模式下，这些调用自动变为
无害的空操作，不需要手动判断。

**正确的启动方式**（仅在 if __name__ == '__main__' 下调用 gui.execute）：

    if __name__ == '__main__':
        gui.execute(main, close_after_done=False)

**无头模式**（不显示 GUI 窗口）：

    python demo.py --no-gui
    python demo.py --headless

在 gui.execute() 内部会自动检测无头模式，不需要手动处理。

**不要在其它位置调用 gui.execute()**。gui.execute 只应出现在主程序
入口的 if __name__ == '__main__' 块中。如果在函数内部调用 gui.execute，
会导致嵌套执行，产生不可预期的行为。

参考 demo 文件（如 zmlx/demos/flow_1ph/darcy_1d.py）了解更多示例。

== 跨线程动界面：四条通道 ==

**控制台线程 / 任意后台线程里，永远不要直接碰 Qt 控件**，按下面的分工选：

======================  ==========================  =========  ===============
想要什么                 用什么                       同步？      拿得到结果
======================  ==========================  =========  ===============
改界面（有导出函数）      ``gui.xxx(...)``             ✅ 阻塞     ✅
改界面（没有导出函数）    ``gui.call(func, ...)``      ✅ 阻塞     ✅
跑长任务                  ``gui.start(func, ...)``     ❌ 立刻返回  `Console.result`
稍后在 GUI 线程跑一下      ``gui.add_task(func)``       ❌          ❌
======================  ==========================  =========  ===============

⚠️ ``gui.start`` 是**单任务**的：控制台只有一个线程槽位，忙的时候再调会被**静默丢弃**
（只响一声）。调之前必须判 ``gui.is_running()`` —— 完整规则、死锁警告与排查表见
[`AGENTS.md`](AGENTS.md) §6。

⚠️ **``Console`` 仍是长任务唯一槽位。** 上表第 3 行说的「跑长任务」= 要能被暂停/停止的
仿真、批量计算。**多个短/中任务并发**是另一件事，用
``zmlx.ui.utils.thread_runner``（§6.8），别反复调 ``gui.start``（第二个必被丢），
也别自己写 ``QThread`` 子类。判据：需要暂停/继续/停止 ⇒ ``gui.start``；
并行做完再回写界面 ⇒ ``thread_runner``。

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
Modified by DeepSeek, 2026-10-20: 补「四条通道」；``call`` / ``start`` / ``add_task``
    由动态代理改为显式方法（带 docstring，便于检索）
Modified by DeepSeek, 2026-10-20: 补「Console 仍是长任务唯一槽位」，指向 thread_runner 的分工
Modified by DeepSeek, 2026-10-23: ``mark_direct`` 补 docstring —— 它去掉的是「派发到 GUI 线程」，
    默认不要用（判据与踩坑见 ``ui/AGENTS.md`` §6.2）
"""

from zmlx.system import warn
import datetime
import os
import sys
from typing import Optional, Tuple, List, Union

from zmlx.system import app_data, is_headless, make_parent


class GuiBuffer:
    def __init__(self):
        self.__api = None

    def command(self, *args, **kwargs):
        """
        执行命令
        Args:
            *args: 位置参数
            **kwargs: 关键词参数
        Returns:
            命令的返回值
        """
        if self.__api is not None:
            return self.__api.command(*args, **kwargs)
        else:
            return None

    def call(self, func, *args, **kwargs):
        """**在 GUI 线程**执行任意可调用对象，并把结果（或异常）带回调用者.

        这是「想动界面，但没有现成的 ``gui.xxx`` 导出函数」时的正道 —— 把要做的
        那一步包成 callable 交给它即可，例如（内核线程里）::

            gui.call(self.btn.setEnabled, False)
            gui.call(lambda: w.setWindowTitle('跑完了'))

        ⚠️ **为什么需要它**：Qt 控件只能在 GUI 线程碰。直接在后台线程
        ``widget.setXxx(...)`` 属未定义行为（轻则不刷新，重则崩）。``GuiApi.command``
        本来就能把「命令名 + 参数」派发过去，``call`` 只是把「命令名」换成「任意
        callable」—— 因此**闭包里的控件访问也在 GUI 线程里发生**。

        ⚠️ 它是**同步**的：调用线程会阻塞到 GUI 线程执行完（异常也会在调用线程重新
        抛出）。所以别在 GUI 线程里调一个「要等内核线程」的东西（会互等死锁），也别
        在持有锁的时候调（GUI 线程可能正等这把锁）。只要「稍后跑一下」、不要结果，
        用 ``add_task`` 而不是它。

        Args:
            func: 要在 GUI 线程执行的可调用对象。
            *args: 传给 ``func`` 的位置参数。
            **kwargs: 传给 ``func`` 的关键词参数。

        Returns:
            ``func`` 的返回值；无界面（headless）时就在当前线程直接执行后返回。
        """
        if self.__api is None:  # 没有界面：不存在「GUI 线程」这件事
            return func(*args, **kwargs)
        return self.command('call', func, *args, **kwargs)

    def start(
            self, func, *, text_beg=None, text_end=None, post_task=None,
            file=None, name=None, add_history=True):
        """在**控制台线程**里执行 ``func`` —— 界面里跑长任务的唯一正规通道.

        转发到 ``Console.start_func``（``main.py`` 里注册为命令 ``start``）。

        ⚠️ **单任务**：控制台只有一个线程槽位，同一时刻只允许一个任务。忙的时候
        再调 ``start`` 会**被直接丢弃**（只响一声 ``play_error()``，没有异常、
        没有返回值区分）。所以调用前请自己判 :meth:`is_running`，并把「忙」如实
        告诉用户 —— 否则用户看到的是「点了没反应」。

        ⚠️ 任务体里操作界面**必须**走 ``gui.xxx`` / :meth:`call` / ``print``
        （``sys.stdout`` 会自己投递到 GUI 线程），不能直接碰控件。

        ⚠️ ``post_task`` 在任务结束后执行，**运行在 GUI 线程**（``Console`` 的
        ``__kernel_exited`` 槽），即使任务抛异常也会执行 —— 适合回写按钮/状态。
        任务的返回值存在 ``Console.result`` 里（``gui.command('get_console')`` 可拿）。

        Args:
            func: 要执行的可调用对象（**不要**传字符串：字符串走 ``exec`` 分支，
                那是给「运行脚本文件」用的）。
            text_beg: 开始提示（蓝色打印到控制台），如 ``'Start: xxx'``。
            text_end: 结束提示。
            post_task: 任务结束后的收尾回调（GUI 线程执行，异常也会执行）。
            file: 记录用的文件名（只影响提示与历史）。
            name: 记录用的 ``__name__``（只影响 ``app_data.space``）。
            add_history: 是否记进「运行历史」（可再点「运行上一次」重跑）。
                临时性任务（例如插件「临时加载」）应当传 ``False``。

        Returns:
            None
        """
        if self.__api is None:  # 无界面：没有控制台线程，直接跑
            try:
                return func()
            finally:
                if callable(post_task):
                    post_task()
        return self.command(
            'start', func, text_beg=text_beg, text_end=text_end,
            post_task=post_task, file=file, name=name,
            add_history=add_history)

    def add_task(self, task):
        """把 ``task`` 投递到 GUI 线程执行（**异步**、不返回结果）.

        与 :meth:`call` 的区别只有两点：不等结果、异常只能靠 ``TaskProc`` 打印。
        高频投递（例如 ``sys.stdout.write``）用它，别用 ``call``。
        """
        api = self.__api
        if api is None:
            return task()
        return api.command('add_task', task)

    def plot(self, kernel, *args, fname=None, dpi=None, caption=None,
             on_top=None, icon=None, clear=None, tight_layout=None,
             suptitle=None, folder_save=None, savefig=None,
             position=None, **kwargs):
        """绘图 —— 渲染留在**调用者自己的线程**，GUI 线程只做「建标签页」和「贴图」。

        ⚠️ 与旧实现的两点区别（2026-10-18 重写 ``MatplotWidget`` 之后）：

        1. **渲染在当前线程完成**。旧实现整条链（含 ``canvas.draw()``）都在 GUI
           线程里，一次重图（contourf / 大量面片，实测数秒）就把界面卡死。现在只有
           「建 / 找标签页」必须回 GUI 线程（约 1 ms）；用户回调与 Agg 渲染都在
           这里做，GUI 线程只贴一张位图（≈ 6 ms）。
        2. **回调里捕获的数据必须是快照**。旧实现是同步的（内核等到画完才走），
           所以「传一个内核正在改写的数组」碰巧安全；现在回调就在**本线程**执行，
           请自己 ``copy()``。

        ⚠️ **返回时机没变**：仍然是「这一帧画完之后」才返回。所以内核连续推图
        不会丢帧 —— 这正是「每次都要接住」的要求（不需要排队，也不需要等待）。

        Args:
            kernel: 绘图的回调函数，函数的原型为：
                def kernel(figure, *args, **kwargs):
                    ...
            *args: 传递给 kernel 函数的参数
            fname: 输出的文件名
            dpi: 输出的分辨率
            caption: 窗口的标题
            on_top: 是否置顶
            icon: 窗口的图标
            clear: 是否清除之前的内容
            tight_layout: 是否自动调整子图参数，以防止重叠
            suptitle: 图表的标题
            folder_save: 自动保存图的文件夹
            savefig: 是否自动保存图（bool，或者文件名）
            position: 标签页的位置（'top' / 'right'）
            **kwargs: 传递给 kernel 函数的关键字参数

        Returns:
            Figure | None: 成功时返回 figure（与旧实现一致）
        """
        if not self.exists():
            return _plot_no_gui(
                kernel, *args, fname=fname, dpi=300 if dpi is None else dpi,
                caption=caption, clear=clear, tight_layout=tight_layout,
                suptitle=suptitle, folder_save=folder_save, **kwargs)
        try:
            # ① GUI 线程：建 / 找标签页（唯一不能在本线程做的事）
            widget = self.command(
                'get_plot_widget', position=position, caption=caption,
                on_top=on_top, icon=icon, folder_save=folder_save)
            if widget is None:
                warn('gui.plot: 无法创建绘图标签页')
                return None
            # ② 本线程：清屏 + 用户回调 + Agg 渲染（耗时全在这里）
            from zmlx.ui.widgets.tab_widget import TabWidget
            on_figure = TabWidget.make_on_figure(
                kernel, args, kwargs,
                clear=True if clear is None else clear,
                suptitle=suptitle, tight_layout=tight_layout)
            if fname is not None:
                savefig = False  # 不自动保存图（下面单独导出）
            widget.plot_on_figure(on_figure=on_figure, savefig=savefig)
            # ③ 本线程：按需导出（内部持锁，且先对齐 figure 尺寸 → 必然清晰）
            if fname is not None:
                if dpi is None:
                    from zmlx.io.env import plt_export_dpi
                    dpi = plt_export_dpi.get_value()
                widget.savefig(fname=fname, dpi=dpi)
            return widget.figure  # 返回 Figure 对象，后续进一步处理
        except Exception as err:
            warn('meet exception <{0}> when run <{1}>'.format(err, kernel))
            return None

    def set(self, api):
        """
        设置api
        Args:
            api: 要设置的api对象
        """
        self.__api = api
        print(f'Gui Set: {self.__api}')

    def get(self):
        """
        返回api对象
        Returns:
            api对象
        """
        return self.__api

    def exists(self):
        """
        是否存在api (处于gui模式下)
        Returns:
            是否存在api对象
        """
        return self.__api is not None

    def __bool__(self):
        """
        是否存在api对象 (处于gui模式下)
        Returns:
            是否存在api对象
        """
        return self.exists()

    def break_point(self):
        """
        添加一个断点，用于暂停以及安全地终止gui程序
        """
        self.command(break_point=True)

    # 函数的别名<为了兼容之前的代码>
    breakpoint = break_point

    def pause(self, message=None):
        """
        点击暂停，并添加断点，确保可以被暂停.
        Args:
            message: 要打印的消息
        """
        if message is not None:
            print(message)
        if is_headless():
            disable = True
        else:
            if app_data is not None:
                disable = app_data.get('DISABLE_PAUSE', False)  # 禁止内核的暂停
            else:
                disable = False
        if not disable:
            self.command('click_pause')
        self.break_point()

    class Agent:
        def __init__(self, obj, name, **opts):
            self.obj = obj
            self.name = name
            self.opts = opts  # 预定义的

        def __call__(self, *args, **kwargs):
            opts = self.opts.copy()
            opts.update(kwargs)
            return self.obj.command(self.name, *args, **opts)

    def __getattr__(self, name):
        """
        返回一个函数代理对象
        Returns:
            函数代理对象
        """
        return GuiBuffer.Agent(self, name)

    def set_agent(self, key, **kwargs):
        """
        添加函数关键词的代理(给定默认值)
        Args:
            key: 函数的名称
            **kwargs: 关键词参数，作为默认值
        Returns:
            函数代理对象
        """
        if len(kwargs) == 0:  # 移除代理
            if hasattr(self, key):
                delattr(self, key)
            return self
        else:  # 添加代理
            agent = GuiBuffer.Agent(self, key, **kwargs)
            setattr(self, key, agent)
            return self

    def mark_direct(self, key):
        """把 ``gui.<key>`` 登记成「**在调用者线程里直接执行**」—— 默认**不要**用.

        语义：登记后 ``gui.<key>(...)`` 不再派发到 GUI 线程，而是在**调用者线程**里
        直接运行那个函数（见 :meth:`GuiApi.command` 的 ``is_direct`` 分支）。它去掉的
        正是「派发到 GUI 线程」这一步。

        ⚠️ **它只在「非 GUI 线程调用」时才有差别**：GUI 线程内调用，正常路径本来就是
        AutoConnection 直连、就地执行，登不登记一模一样。所以 ``is_direct`` 的全部
        意义都落在后台线程那条路上 —— 而那正是最危险的一条。

        ⚠️ **判据只有一条：函数体不触碰任何 Qt 对象**。目前全仓**只有 ``window``**
        符合（就是 ``lambda: self``，只返回 ``MainWindow`` 实例本身）。

        它换来的是**确定的延迟上界**（2026-10-30 实测：GUI 线程在槽里阻塞 1.5 s 期间，
        从后台线程调 ``gui.window()``）：

        ======================  ===========
        走法                     耗时
        ======================  ===========
        ``is_direct``（登记后）   **0.023 ms**
        正常派发                 **1200 ms**（一直等到 GUI 回到事件循环）
        ======================  ===========

        ⚠️ 这里的「GUI 忙」指**阻塞了事件循环**（长槽里的计算 / 文件 IO）；模态对话框
        自带事件循环，不会拖住排队的调用。两者都拿到同一个窗口对象 ⇒ **正确性无差别，
        差别只在延迟**。

        ❌ **凡是会建控件、碰窗口、读标签容器的命令都不能登记**，哪怕它只是「转发」：
        一旦登记，后台线程（控制台 / 插件）调 ``gui.xxx()`` 就**当场在后台线程里**
        建控件 —— Qt 控件只能在 GUI 线程碰，轻则不刷新、重则崩，且不可复现。
        2026-10-23 就因为「以为转发类方法多绕了一跳」把 14 条插件命令登记过，当日撤销。

        ⚠️ **2026-10-30 又撤了 ``edit_in_tab`` / ``reg_file_type`` 两条**：前者全部工作就是
        调 ``gui.get_widget(...)``（登记成 direct = 在后台线程里调 GUI 命令，绕一圈没有
        收益），后者只做注册、GUI 线程执行一样快。**它们换不到上表那个延迟收益，只会多
        一份「在后台线程执行」的风险面。**

        ⚠️ **「多绕了一跳」不构成理由**：命令表里放的往往是插件函数本身
        （``gui.add_func`` 后写覆盖），主窗口经 ``gui.xxx`` 是「GUI 线程内直接执行」；
        嫌绕就直接调那个对象（``w.show_timer()``），不要改这里的线程语义。
        通道池取消之后（v1.9.9），连「省一个通道」这条老理由也不成立了。

        Args:
            key: 函数的名称。
        Returns:
            函数代理对象（``self``）。
        """
        return self.set_agent(key, is_direct=True)

    def execute(
            self, func=None, keep_cwd=True, close_after_done=True,
            args=None,
            kwargs=None, disable_gui=False, add_history=True):
        """
        尝试在gui模式下运行给定的函数 func
        Args:
            func: 要运行的函数
            keep_cwd: 是否保持当前目录
            close_after_done: 是否在完成后关闭gui
            args: 要传递给函数的位置参数
            kwargs: 要传递给函数的关键词参数
            disable_gui: 是否禁用gui模式
            add_history: 是否将运行历史添加到历史记录(从而方便再次运行)
        Returns:
            函数的返回值
        """

        def fx():
            if func is not None:
                x = args if args is not None else []
                y = kwargs if kwargs is not None else {}
                return func(*x, **y)
            else:
                return None

        from zmlx.system import is_headless

        if self.exists() or disable_gui or is_headless():  # 此时，不需要新启动GUI界面
            return fx()

        try:
            from zmlx.ui.main import execute
            return execute(fx, keep_cwd=keep_cwd,
                           close_after_done=close_after_done,
                           add_history=add_history)
        except Exception as execute_err:
            print(f'call gui failed: {execute_err}', file=sys.stderr)
            return fx()


gui = GuiBuffer()

app_data.put('gui', gui)


def break_point():
    """
    添加一个gui的断点，从而在gui执行的过程中，可以控制暂停和终止
    """
    gui.break_point()


def information(*args, **kwargs):
    break_point()
    return gui.information(*args, **kwargs)


def question(info):
    if gui.exists():
        break_point()
        return gui.question(info)
    else:
        y = input(f"{info} input 'y' or 'Y' to continue: ")
        return y == 'y' or y == 'Y'


def _plot_no_gui(kernel, *args, fname=None, dpi=300, caption=None, clear=None, tight_layout=None, suptitle=None,
                 on_top=None,  # 兼容gui下的参数
                 savefig=None,  # 兼容gui下的参数
                 folder_save=None,  # 兼容gui下的参数
                 **kwargs):
    """在非 GUI 模式下绘图（保存到文件）。

    内部函数，用户不应直接调用。请使用 gui.plot() 或 zmlx.ui.plot()，
    它们会自动根据环境选择 GUI 绘图或非 GUI 保存。
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        from zmlx.system import log
        log(text=f'{e}', tag='matplotlib_import_error')
        plt = None

    if kernel is None or plt is None:
        return None
    try:
        from zmlx.plt import set_chinese_font
        set_chinese_font()

        if fname is None:
            if folder_save is not None:
                now = datetime.datetime.now()
                name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}.png"
                fname = make_parent(os.path.join(folder_save, name))
            else:
                if is_headless() and caption is None:
                    caption = "default_figure"
                if caption is not None:
                    from zmlx.plt import get_plt_save_path
                    now = datetime.datetime.now()
                    name = now.strftime("%Y-%m-%d-%H-%M-%S-") + f"{now.microsecond:06d}.png"
                    fname = make_parent(os.path.join(get_plt_save_path(caption), name))
        fig = plt.figure()
        kernel(fig, *args, **kwargs)
        if isinstance(suptitle, str):
            fig.suptitle(suptitle)
        if tight_layout:
            if isinstance(tight_layout, dict):
                fig.tight_layout(**tight_layout)
            else:
                fig.tight_layout()
        if fname is not None:
            fig.savefig(fname=fname, dpi=dpi)
            plt.close()
            return None
        else:
            plt.show()
            return fig
    except Exception as err:
        warn(f'meet exception <{err}> when run <{kernel}>')
        return None


def plot(kernel, *args, gui_only=False, gui_mode=None,
         fname=None, dpi=300,
         **kwargs):
    """
    调用matplotlib执行绘图操作. 如果需要处于gui_mode下面绘图，但是当前不是gui模式，则打开gui界面绘图(此功能仅供测试使用)
    Args:
        kernel: 绘图的回调函数，函数的原型为：
            def kernel(figure, *args, **kwargs):
                ...
        gui_only: 是否只在GUI模式下执行
        fname: 输出的文件名
        dpi: 输出的分辨率
        *args: 传递给kernel函数的参数
        **kwargs: 传递给kernel函数的关键字参数
        gui_mode: 是否强制使用GUI模式
    Returns:
        None
    """

    def plot_with_gui():
        try:
            gui.break_point()
            return gui.plot(kernel, *args, fname=fname, dpi=dpi, **kwargs)
        except Exception as plot_err:
            print(f'plot failed: {plot_err}', file=sys.stderr)
            return None

    if gui.exists():
        return plot_with_gui()

    # 此时，没有处在gui中
    if gui_mode:
        from zmlx.system import is_headless
        if is_headless():
            gui_mode = False

    if gui_mode:  # 创建窗口来运行(并在绘图后保持窗口打开状态)
        return gui.execute(plot_with_gui, close_after_done=False)

    if gui_only:
        return None
    else:
        return _plot_no_gui(kernel, *args, fname=fname, dpi=dpi, **kwargs)


def progress(
        label: Optional[str] = None, val_range: Optional[Union[List[int], Tuple[int, int]]] = None,
        value: Optional[int] = None, visible: Optional[bool] = None
):
    """
    显示(或者隐藏进度条(如果gui模式下)
    Args:
        label: 进度条的标签
        val_range: 进度条的范围
        value: 当前进度
        visible: 是否可见
    Returns:
        None
    """
    if gui.exists():
        gui.progress(label=label, val_range=val_range, value=value, visible=visible)


def show_attrs(clear: bool = False, **attrs):
    """
    在控制台内核运行的过程中，在控制台的输出窗口显示的一些动态的属性值（在控制台运行结束之后隐藏）
    Args:
        clear: 是否清除已有的参数
        **attrs: 要显示的参数
    Returns:
        None
    """
    if gui.exists():
        gui.show_attrs(clear=clear, **attrs)


def gui_exec(*args, **kwargs):
    """
    调用gui来执行一个函数，并返回函数的执行结果
    """
    return gui.execute(*args, **kwargs)


def add_action(
        menu=None, text=None, name=None, slot=None,
        icon=None, tooltip=None, shortcut=None,
        on_toolbar=None,
        is_enabled=None,
        is_visible=None,
        overwritable=None,
        overwrite=None
):
    """
    在gui菜单添加一个操作项

    参数原样转给 ``MainWindow.add_action``（同步派发到 GUI 线程执行），**这里不加逻辑**；
    完整的参数说明见那个方法的 docstring。两个要点在这里重复一次，因为最常踩：

    - ``menu`` 可以是 ``str``（一级）或 ``list``（多级路径），每级标题必须与别处**逐字一致**；
    - ``overwrite`` 管的是「**``name`` 已被占用时怎么办**」：
      ``True``（默认）→ **就地覆盖**：用本次参数重设那个已有 action（菜单里始终只有一条）；
      ``False`` → 发一条 ``UserWarning`` 并**跳过**，已有那条保持原样。

    ⚠️ ``overwritable`` 是 ``overwrite`` 的**弃用别名**（2026-10-27 改名，2027-10-27 删除）：
    传它会发一条 ``DeprecationWarning``，行为与 ``overwrite`` 完全等价。新代码请用 ``overwrite``。

    ⚠️ ``text='---'`` 是**分隔符**（2026-10-26 加；判据是 ``text`` 而非 ``name``）：
    只在菜单末尾插一条分隔线，不建 action —— 其余参数一个都不用给::

        gui.add_action(menu='操作', text='---')

    它**不判重**（连插两条就是两条线），也**不会**让分隔线出现在工具栏上
    （``on_toolbar`` 对它不生效；工具栏的分隔符仍要自己 ``insertSeparator``）。
    """
    if gui.exists():
        gui.add_action(
            menu=menu, text=text, name=name, slot=slot,
            icon=icon, tooltip=tooltip, shortcut=shortcut,
            on_toolbar=on_toolbar,
            is_enabled=is_enabled,
            is_visible=is_visible,
            overwritable=overwritable,
            overwrite=overwrite
        )


def proc_argv(argv=None):
    from zmlx.algs import fsys
    if not isinstance(argv, (list, tuple)):
        return
    if len(argv) < 2:
        return
    key = argv[1]
    if fsys.isfile(key):
        gui.open_file(key)
        return
    gui.command(*argv[1:])


def open_gui(argv=None):
    """
    打开gui
    """
    from zmlx.system import app_data
    app_data.put('argv', argv)
    # 是否需要恢复标签
    app_data.put('restore_tabs',
                 app_data.getenv('restore_tabs', default='Yes') != 'No')
    # 是否初始检查
    app_data.put('init_check',
                 app_data.getenv('init_check', default='Yes') != 'No')
    gui.execute(func=lambda: proc_argv(argv), keep_cwd=False, close_after_done=False,
                add_history=False)


def open_gui_without_setup(argv=None):
    """打开界面，但**本次不执行任何插件**（``plugins.load_all()`` 被跳过）.

    ⚠️ 这是「这一次不跑插件」的**唯一**开关 —— 它是**运行时**状态（``app_data.put``，
    只活在内存里），不会写盘、也不会改变任何持久设置。想永久不跑某个插件，请用
    「设置 → 插件」里那一行（``plugins.set_disabled``）。

    ⚠️ 两个键都写（2026-10-22）：``run_plugins`` 是新名，``run_setup`` 是旧名
    （``zml_gui_setup.py`` 那个文件名的残留）。``main.py`` 的 ``__console_kernel`` 先读
    新名、取不到回落旧名 —— 两个都写是为了「万一还有别处的旧版 ``main.py`` 读旧名」。
    """
    from zmlx.system import app_data
    app_data.put('argv', argv)
    app_data.put('restore_tabs', False)
    app_data.put('run_plugins', False)   # 新名（main.py 优先读它）
    app_data.put('run_setup', False)     # 旧名（兼容，2027-10-22 删）
    gui.execute(func=lambda: proc_argv(argv), keep_cwd=False, close_after_done=False, add_history=False)


def test():
    import sys
    open_gui(sys.argv)


if __name__ == "__main__":
    test()
